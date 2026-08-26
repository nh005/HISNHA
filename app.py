import streamlit as st
import time
import re
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal
from urllib.parse import quote


st.set_page_config(
    page_title="HISNHA | حصنها",
    page_icon="🛡️",
    layout="centered",
)


# -----------------------------
# Session state
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "lang" not in st.session_state:
    st.session_state.lang = "EN"

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


# -----------------------------
# Language selector
# -----------------------------
# A compact pill-style language switcher. It moves with the page direction:
# right side in English, left side in Arabic.
current_language_label = "العربية" if st.session_state.lang == "AR" else "English"

if st.session_state.lang == "AR":
    toggle_col, globe_col, spacer_col = st.columns([2.4, 0.35, 4.6])
else:
    spacer_col, globe_col, toggle_col = st.columns([4.6, 0.35, 2.4])

with globe_col:
    st.markdown(
        "<div style='padding-top:7px;text-align:center;font-size:20px;'>🌐</div>",
        unsafe_allow_html=True,
    )

with toggle_col:
    if hasattr(st, "pills"):
        selected_language = st.pills(
            "Language / اللغة",
            options=["العربية", "English"],
            default=current_language_label,
            selection_mode="single",
            label_visibility="collapsed",
            width="stretch",
            key="language_pills",
        )
    else:
        # Fallback for older Streamlit versions.
        selected_language = st.radio(
            "Language / اللغة",
            options=["العربية", "English"],
            index=0 if st.session_state.lang == "AR" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="language_pills_fallback",
        )

if selected_language is None:
    selected_language = current_language_label

new_lang = "AR" if selected_language == "العربية" else "EN"
if new_lang != st.session_state.lang:
    st.session_state.lang = new_lang
    st.session_state.analysis_result = None
    st.rerun()

LANG = st.session_state.lang


# -----------------------------
# RTL / LTR styling + typography
# -----------------------------
# Typography only: the original HISNHA colors, spacing, cards, and button layout stay unchanged.
if LANG == "AR":
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap');

        [data-testid="stAppViewContainer"] .main .block-container {
            direction: rtl;
            text-align: right;
        }
        [data-testid="stMarkdownContainer"],
        [data-testid="stWidgetLabel"],
        [data-testid="stText"],
        .stButton button,
        .stLinkButton a,
        .stTextArea textarea,
        .stTextInput input {
            font-family: "Cairo", Tahoma, Arial, sans-serif !important;
        }
        [data-testid="stMarkdownContainer"],
        [data-testid="stWidgetLabel"] {
            direction: rtl;
            text-align: right;
        }
        .stTextArea textarea,
        .stTextInput input {
            direction: rtl;
            text-align: right;
        }
        .stButton button,
        .stLinkButton a {
            direction: rtl;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        [data-testid="stMarkdownContainer"],
        [data-testid="stWidgetLabel"],
        [data-testid="stText"],
        .stButton button,
        .stLinkButton a,
        .stTextArea textarea,
        .stTextInput input {
            font-family: "Inter", "Segoe UI", Arial, sans-serif !important;
        }
        [data-testid="stAppViewContainer"] .main .block-container {
            direction: ltr;
            text-align: left;
        }
        .stTextArea textarea,
        .stTextInput input {
            direction: ltr;
            text-align: left;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Small helpers
# -----------------------------
def tr(en: str, ar: str) -> str:
    return ar if LANG == "AR" else en


def go_to(page_name: str):
    st.session_state.page = page_name
    st.rerun()


def back_home():
    if st.button(tr("← Back to Home", "العودة إلى الرئيسية →"), use_container_width=True):
        go_to("home")


def get_gemini_client():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        return genai.Client(api_key=api_key)
    except Exception:
        return None



def soft_card(text_value: str, kind: str = "info", margin_top: int = 8, margin_bottom: int = 14):
    """Warm HISNHA-style information cards used across the app."""
    palette = {
        "info": {"bg": "#C4C0E3", "text": "#21529D"},
        "warning": {"bg": "#D9CDCE", "text": "#8C6D23"},
        "danger": {"bg": "#D6B8CF", "text": "#AF4947"},
        "remember": {"bg": "#C4C0E3", "text": "#21529D"},
        "neutral": {"bg": "#D8C7E3", "text": "#4B3C55"},
    }
    colors = palette.get(kind, palette["info"])
    st.markdown(
        f"""
        <div style="
            padding:16px 18px;
            border-radius:12px;
            background:{colors['bg']};
            color:{colors['text']};
            font-size:16px;
            line-height:1.65;
            margin:{margin_top}px 0 {margin_bottom}px 0;
        ">
            {text_value}
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# AI structured output
# -----------------------------
# Keep threat labels controlled so the experience feels consistent from one analysis to another.
ThreatType = Literal[
    "NO_THREAT",
    "SOCIAL_ENGINEERING",
    "PHISHING",
    "SUSPICIOUS_LINK",
    "ACCOUNT_TAKEOVER",
    "IMPERSONATION",
    "ONLINE_HARASSMENT",
    "BLACKMAIL_EXTORTION",
]


class SafetyAnalysis(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    threat_type: ThreatType
    reasons: list[str]
    actions: list[str]


THREAT_LABELS = {
    "NO_THREAT": {"en": "No Threat Detected", "ar": "لا يوجد تهديد واضح"},
    "SOCIAL_ENGINEERING": {"en": "Social Engineering", "ar": "هندسة اجتماعية"},
    "PHISHING": {"en": "Phishing", "ar": "تصيد احتيالي"},
    "SUSPICIOUS_LINK": {"en": "Suspicious Link", "ar": "رابط مشبوه"},
    "ACCOUNT_TAKEOVER": {"en": "Account Takeover Attempt", "ar": "محاولة الاستيلاء على الحساب"},
    "IMPERSONATION": {"en": "Impersonation", "ar": "انتحال شخصية أو صفة"},
    "ONLINE_HARASSMENT": {"en": "Online Harassment", "ar": "تحرش إلكتروني"},
    "BLACKMAIL_EXTORTION": {"en": "Blackmail / Extortion", "ar": "ابتزاز إلكتروني / تهديد"},
}


def analyze_message(message: str, output_language: str) -> SafetyAnalysis:
    client = get_gemini_client()
    if client is None:
        raise RuntimeError("GEMINI_API_KEY_NOT_FOUND")

    # Keep the security signal of a link without asking the model to visit it.
    contains_url = bool(re.search(r"(?:https?://|www\.)\S+", message, flags=re.IGNORECASE))
    message_for_analysis = re.sub(
        r"(?:https?://|www\.)\S+",
        "[URL_PRESENT]",
        message,
        flags=re.IGNORECASE,
    )

    url_context = (
        "The original message contains a URL. Treat [URL_PRESENT] as an untrusted-link placeholder. "
        "Do not visit it; evaluate the surrounding wording and behavior only."
        if contains_url
        else
        "The original message does not contain a URL."
    )

    if output_language == "AR":
        language_instruction = """
Write the reasons and actions in clear, natural Modern Standard Arabic.
The primary audience is women and girls, so feminine wording may be used naturally when it makes the guidance feel supportive,
but do not make the text awkwardly gender-exclusive. Use clear, direct safety language.
Do not add numbering, bullets, emojis, headings, or labels inside reasons or actions because the interface adds them.
"""
    else:
        language_instruction = """
Write the reasons and actions in clear, natural English.
Use a calm, supportive, human tone for a non-expert user.
Do not add numbering, bullets, emojis, headings, or labels inside reasons or actions because the interface adds them.
"""

    prompt = f"""
You are HISNHA, a digital-safety assistant designed for non-expert users.
Analyze ONLY the message below. This is a defensive cybersecurity and online-safety task.
Do not open, visit, or follow any URL.

VOICE AND QUALITY:
- Sound calm, supportive, practical, and human — not robotic or generic.
- Explain the specific clues you noticed and WHY they matter.
- Tailor the safety steps to the exact situation instead of repeating the same generic advice every time.
- Be concise enough to scan, but detailed enough that the user understands what is happening.
- Avoid blame, panic, or dramatic wording.
- Avoid unsupported absolute claims about companies, platforms, support teams, banks, or other organizations.
- Do NOT say things like "legitimate services will never..." or "a platform will always...".
- Describe the risky behavior instead, for example: "A request to share a verification code with another person is a strong warning sign and can put the account at risk."
- You may still give firm user-safety guidance when appropriate, such as: "Never share your password or verification code with another person."
- For harassment, blackmail, or threats, prioritize evidence preservation and personal safety.

OUTPUT LANGUAGE:
{language_instruction}

RISK LEVEL RULES:

LOW:
- Ordinary, harmless, or informational message.
- No meaningful pressure, deception, threats, suspicious links, or requests for sensitive information.

MEDIUM:
- Suspicious urgency, pressure, manipulation, vague account claims, unexpected requests, or concerning behavior.
- The situation deserves caution, but there is not enough evidence for a high-risk classification.
- Mild or ambiguous unwanted contact may be MEDIUM.

HIGH:
- Direct request for a password, OTP, verification code, login credential, banking/payment information, or highly sensitive data.
- Credential theft, account takeover, credential harvesting, or deceptive sign-in/payment request.
- Blackmail, extortion, threats involving private/intimate material, stalking-like behavior, doxxing, credible threats, or severe targeted harassment.
- A suspicious link combined with urgency and a request to sign in, verify identity, pay, or provide sensitive information.
- Harmful impersonation combined with a dangerous request.

THREAT TYPE TAXONOMY — choose EXACTLY ONE:
- NO_THREAT: ordinary/informational with no meaningful threat.
- SOCIAL_ENGINEERING: manipulation, urgency, or pressure without a stronger category.
- PHISHING: deceptive attempt to make the user sign in, reveal data, click a deceptive link, or take an unsafe action.
- SUSPICIOUS_LINK: the unexpected/suspicious link is the main concern and stronger phishing evidence is limited.
- ACCOUNT_TAKEOVER: asks for OTP, verification code, password, login credential, or clearly aims to control the account.
- IMPERSONATION: falsely claims to be a person, support team, institution, or trusted party.
- ONLINE_HARASSMENT: abusive, intimidating, sexual, persistent, stalking-like, or repeated unwanted online behavior.
- BLACKMAIL_EXTORTION: threats to expose, harm, or publish private content/information unless the user pays or complies.

OUTPUT QUALITY RULES:
- LOW: usually 2–3 reasons and 1–3 proportionate actions.
- MEDIUM/HIGH: usually 3 reasons and 3–5 practical actions.
- Blackmail/extortion may use up to 5 actions when evidence preservation and account/payment safety are important.
- Each reason should be a complete, natural sentence explaining one specific signal.
- Each action should be a practical, complete sentence.
- Do not include numbering or bullet characters in reasons/actions.
- If LOW, explain why the message appears safe rather than calling it suspicious.
- For blackmail/extortion, preserve evidence BEFORE recommending blocking/deleting.
- If there is possible immediate real-world danger, advise prioritizing personal safety and seeking appropriate local help.
- Base the result only on evidence present in the message.

Return ONLY the structured result required by the schema.

URL CONTEXT:
{url_context}

USER MESSAGE:
{message_for_analysis}
"""

    last_error = None

    # One immediate request + limited retry only for temporary server-side failures.
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=SafetyAnalysis,
                ),
            )

            analysis = response.parsed
            if analysis is None:
                if not getattr(response, "text", None):
                    raise RuntimeError("EMPTY_AI_RESPONSE")
                return SafetyAnalysis.model_validate_json(response.text)

            if isinstance(analysis, dict):
                return SafetyAnalysis.model_validate(analysis)

            return analysis

        except Exception as error:
            last_error = error
            error_text = str(error).upper()
            print(f"HISNHA Gemini analysis error (attempt {attempt + 1}/2): {repr(error)}")

            # Do not burn extra quota by retrying a rate-limit/quota error.
            if (
                "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
                or "RATE" in error_text
                or "QUOTA" in error_text
            ):
                raise error

            transient = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "500" in error_text
                or "DEADLINE" in error_text
            )
            if attempt == 0 and transient:
                time.sleep(1.5)
                continue

            raise error

    raise last_error

# -----------------------------
# Shared educational video helper
# -----------------------------
def watch_and_learn(video_id: str, caption_en: str, caption_ar: str, resource_url: str, resource_name: str):
    st.markdown(tr("### 🎥 Watch & Learn", "### 🎥 شاهد وتعلّم"))
    st.image(f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg", use_container_width=True)
    st.video(f"https://www.youtube.com/watch?v={video_id}")
    st.caption(tr(caption_en, caption_ar))
    st.link_button(
        tr(f"🔗 Learn More — {resource_name}", f"🔗 مصدر إضافي — {resource_name}"),
        resource_url,
        use_container_width=True,
    )


# -----------------------------
# Home
# -----------------------------
def render_home():
    # Keep the original HISNHA visual layout used in the Concept Note and slides.
    logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
    with logo_col2:
        st.image("assets/hisnha_logo.png", use_container_width=True)

    st.write(
        tr(
            "An AI-powered digital safety platform designed to help women and girls recognize online threats, strengthen their privacy, and respond safely to digital risks.",
            "منصة ذكية للسلامة الرقمية مدعومة بالذكاء الاصطناعي، صُممت أساسًا لمساعدة النساء والفتيات على التعرّف على التهديدات الإلكترونية، وتعزيز الخصوصية، والاستجابة للمخاطر الرقمية بطريقة آمنة وواضحة، مع بقاء الأدوات متاحة لأي مستخدم يمكن أن يستفيد منها.",
        )
    )

    st.divider()
    st.markdown(tr("## How can we help you?", "## كيف يمكن أن نساعدك؟"))

    # Original button order: Check a Message + I Need Help, then Privacy Checkup + Learn.
    col1, col2 = st.columns(2)
    with col1:
        if st.button(tr("🔍 Check a Message", "🔍 فحص رسالة"), type="primary", use_container_width=True):
            go_to("check_message")
    with col2:
        if st.button(tr("🛡️ I Need Help", "🛡️ أحتاج مساعدة"), use_container_width=True):
            go_to("help")

    col3, col4 = st.columns(2)
    with col3:
        if st.button(tr("🔐 Privacy Checkup", "🔐 فحص الخصوصية"), use_container_width=True):
            go_to("privacy")
    with col4:
        if st.button(tr("📚 Learn", "📚 تعلّم"), use_container_width=True):
            go_to("learn")

    st.divider()
    st.caption(
        tr(
            "🔒 Your privacy matters. Never enter passwords, OTP codes, private images, or highly sensitive personal information.",
            "🔒 خصوصيتك مهمة. لا تُدخل كلمات المرور أو رموز OTP أو الصور الخاصة أو أي معلومات شخصية شديدة الحساسية.",
        )
    )


# -----------------------------
# Check a Message
# -----------------------------
def render_check_message():
    back_home()
    st.title(tr("🔍 Check a Message", "🔍 فحص رسالة"))
    st.write(
        tr(
            "Enter a message you are unsure about. HISNHA will look for digital-safety warning signs, explain what they mean, and suggest practical next steps.",
            "أدخلي رسالة تشعرين بعدم الارتياح تجاهها، وستبحث حِصنها عن مؤشرات الخطر الرقمي، وتشرح معناها، وتقترح خطوات عملية للتعامل معها.",
        )
    )

    message = st.text_area(
        tr("Message to analyze", "الرسالة المراد تحليلها"),
        height=160,
        placeholder=tr(
            "Enter your message here...",
            "اكتب الرسالة هنا...",
        ),
        key="message_input",
    )

    # Keep this as a light line under the message box — not another large card.
    st.markdown(
        tr(
            "<span style='color:#655C6D;font-size:14px;'>⚠️ Do not enter passwords, OTP codes, phone numbers, banking details, private images, or other highly sensitive personal information.</span>",
            "<span style='color:#655C6D;font-size:14px;'>⚠️ لا تُدخلي كلمات المرور أو رموز OTP أو أرقام الهواتف أو المعلومات البنكية أو الصور الخاصة أو أي معلومات شخصية شديدة الحساسية.</span>",
        ),
        unsafe_allow_html=True,
    )

    if st.button(tr("🔍 Analyze Message", "🔍 تحليل الرسالة"), type="primary", use_container_width=True):
        if not message.strip():
            st.warning(tr("Please enter a message first.", "يرجى إدخال رسالة أولًا."))
        else:
            try:
                with st.spinner(
                    tr(
                        "🛡️ HISNHA is analyzing your message...",
                        "🛡️ حِصنها تحلل الرسالة الآن...",
                    )
                ):
                    st.session_state.analysis_result = analyze_message(message.strip(), LANG)

            except Exception as error:
                error_text = str(error)
                if "GEMINI_API_KEY_NOT_FOUND" in error_text:
                    st.error(
                        tr(
                            "Gemini API key was not found in Streamlit Secrets.",
                            "لم يتم العثور على مفتاح Gemini API داخل Streamlit Secrets.",
                        )
                    )
                elif (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text.upper()
                    or "RATE" in error_text.upper()
                    or "QUOTA" in error_text.upper()
                ):
                    st.warning(
                        tr(
                            "The AI request limit was reached temporarily. Please wait and try again later.",
                            "تم الوصول مؤقتًا إلى حد طلبات الذكاء الاصطناعي. انتظري قليلًا ثم حاولي مرة أخرى لاحقًا.",
                        )
                    )
                elif (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text.upper()
                    or "500" in error_text
                    or "DEADLINE" in error_text.upper()
                ):
                    st.warning(
                        tr(
                            "The AI service is temporarily busy. Please try again in a moment.",
                            "خدمة الذكاء الاصطناعي مشغولة مؤقتًا. حاولي مرة أخرى بعد قليل.",
                        )
                    )
                else:
                    st.error(
                        tr(
                            "We could not analyze the message right now. Please try again.",
                            "تعذر تحليل الرسالة حاليًا. يرجى المحاولة مرة أخرى.",
                        )
                    )

    analysis = st.session_state.analysis_result
    if analysis is not None:
        st.divider()
        st.subheader(tr("🛡️ HISNHA Safety Analysis", "🛡️ تحليل حِصنها للسلامة الرقمية"))

        risk_display = {
            "LOW": {
                "label_en": "🟢 LOW RISK",
                "label_ar": "🟢 خطر منخفض",
                "text": "#3A8D3F",
                "bg": "#C5C6D3",
            },
            "MEDIUM": {
                "label_en": "🟠 MEDIUM RISK",
                "label_ar": "🟠 خطر متوسط",
                "text": "#8C6D23",
                "bg": "#D9CDCE",
            },
            "HIGH": {
                "label_en": "🔴 HIGH RISK",
                "label_ar": "🔴 خطر مرتفع",
                "text": "#AF4947",
                "bg": "#D6B8CF",
            },
        }

        risk = risk_display[analysis.risk_level]
        risk_label = risk["label_ar"] if LANG == "AR" else risk["label_en"]

        st.markdown(
            f"""
            <div style="
                padding:17px 18px;
                border-radius:12px;
                background:{risk['bg']};
                color:{risk['text']};
                font-weight:700;
                font-size:18px;
                margin:6px 0 22px 0;
            ">
                {risk_label}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(tr("### ⚠️ Threat Type", "### ⚠️ نوع التهديد"))
        threat_label = THREAT_LABELS[analysis.threat_type]["ar" if LANG == "AR" else "en"]
        soft_card(threat_label, "info", margin_top=6, margin_bottom=22)

        if analysis.risk_level == "LOW":
            st.markdown(
                tr(
                    "### 🔎 Why does this message appear safe?",
                    "### 🔎 لماذا تبدو هذه الرسالة آمنة؟",
                )
            )
        else:
            st.markdown(
                tr(
                    "### 🔎 Why is this suspicious?",
                    "### 🔎 لماذا قد تكون هذه الرسالة خطرة؟",
                )
            )

        for reason in analysis.reasons:
            st.write(f"• {reason}")

        st.markdown(tr("### 🛡️ What should you do?", "### 🛡️ ما الخطوة المناسبة الآن؟"))
        for number, action in enumerate(analysis.actions, start=1):
            st.write(f"{number}. {action}")

        st.divider()

        remember_text = tr(
            "💜 <b>Remember:</b> Never share passwords, OTP codes, verification codes, or other highly sensitive personal information.",
            "💜 <b>تذكير:</b> لا تشاركي كلمات المرور أو رموز OTP أو رموز التحقق أو أي معلومات شخصية شديدة الحساسية.",
        )
        soft_card(remember_text, "remember", margin_top=8, margin_bottom=12)

    st.caption(
        tr(
            "HISNHA provides digital-safety guidance. The current prototype does not save the message in its own database.",
            "تقدّم حِصنها إرشادات للسلامة الرقمية، ولا يحفظ النموذج الأولي الحالي الرسالة في قاعدة بيانات خاصة به.",
        )
    )

# -----------------------------
# Privacy Checkup
# -----------------------------
PRIVACY_QUESTIONS = [
    {
        "en": "Do you use two-factor authentication (2FA) on important accounts?",
        "ar": "هل تستخدمين المصادقة الثنائية (2FA) على الحسابات المهمة؟",
        "rec_en": "Turn on two-factor authentication for important accounts whenever it is available.",
        "rec_ar": "فعّلي المصادقة الثنائية للحسابات المهمة كلما كانت متاحة.",
    },
    {
        "en": "Do you use a different password for each important account?",
        "ar": "هل تستخدمين كلمة مرور مختلفة لكل حساب مهم؟",
        "rec_en": "Use unique passwords so one leaked password does not expose several accounts.",
        "rec_ar": "استخدمي كلمات مرور مختلفة حتى لا يؤدي تسريب كلمة واحدة إلى تعريض عدة حسابات للخطر.",
    },
    {
        "en": "Do you regularly review devices or sessions logged in to your accounts?",
        "ar": "هل تراجعين بانتظام الأجهزة أو الجلسات المسجل دخولها إلى حساباتك؟",
        "rec_en": "Review active sessions and sign out devices you do not recognize.",
        "rec_ar": "راجعي جلسات تسجيل الدخول وأخرجي أي جهاز لا تعرفينه.",
    },
    {
        "en": "Do you avoid opening suspicious links from unknown or unexpected senders?",
        "ar": "هل تتجنبين فتح الروابط المشبوهة من مرسلين غير معروفين أو غير متوقعين؟",
        "rec_en": "Avoid opening unexpected links. Verify the request using the official app or website instead.",
        "rec_ar": "تجنّبي فتح الروابط غير المتوقعة، وتحققي من الطلب من خلال التطبيق أو الموقع الرسمي بدلًا من ذلك.",
    },
    {
        "en": "Do you review the privacy settings of your social media accounts?",
        "ar": "هل تراجعين إعدادات الخصوصية في حسابات التواصل الاجتماعي؟",
        "rec_en": "Review who can see your posts, location, contact information, and account activity.",
        "rec_ar": "راجعي من يستطيع رؤية منشوراتك وموقعك ومعلومات التواصل ونشاط الحساب.",
    },
]


def render_privacy_checkup():
    back_home()
    st.title(tr("🔐 Privacy Checkup", "🔐 فحص الخصوصية"))
    st.write(
        tr(
            "Answer five simple questions to review some of your current digital-safety habits.",
            "أجيبي عن خمسة أسئلة بسيطة لمراجعة بعض عادات الأمان الرقمي لديك.",
        )
    )

    st.caption(
        tr(
            "All five questions are required.",
            "جميع الأسئلة الخمسة مطلوبة.",
        )
    )

    answers = []
    for index, question in enumerate(PRIVACY_QUESTIONS):
        answer = st.radio(
            tr(question["en"], question["ar"]),
            options=[True, False],
            format_func=lambda value: tr("Yes", "نعم") if value else tr("No", "لا"),
            index=None,
            key=f"privacy_q_{index}",
        )
        answers.append(answer)

    all_answered = all(answer is not None for answer in answers)

    if st.button(
        tr("✨ Show My Result", "✨ إظهار النتيجة"),
        type="primary",
        use_container_width=True,
        disabled=not all_answered,
    ):
        score = sum(20 for answer in answers if answer)
        st.session_state.privacy_score = score
        st.session_state.privacy_answers = answers

    # Never show a result unless every question has been answered.
    if "privacy_score" in st.session_state and all_answered:
        score = st.session_state.privacy_score
        answers = st.session_state.privacy_answers

        st.divider()
        st.metric(tr("Digital Safety Score", "درجة الأمان الرقمي"), f"{score}/100")
        st.progress(score / 100)

        if score >= 80:
            st.success(tr("Strong habits — keep maintaining them.", "عادات قوية — استمري بالمحافظة عليها."))
        elif score >= 60:
            st.warning(tr("Good start — a few improvements can make your accounts safer.", "بداية جيدة — بعض التحسينات يمكن أن تجعل حساباتك أكثر أمانًا."))
        else:
            st.error(tr("Some important safety habits need attention.", "بعض عادات الأمان المهمة تحتاج إلى انتباه."))

        recommendations = []
        for answer, question in zip(answers, PRIVACY_QUESTIONS):
            if not answer:
                recommendations.append(tr(question["rec_en"], question["rec_ar"]))

        if recommendations:
            st.markdown(tr("### Recommendations", "### توصيات"))
            for recommendation in recommendations:
                st.write(f"• {recommendation}")

    st.caption(
        tr(
            "This is an awareness checkup, not a complete cybersecurity assessment.",
            "هذا فحص توعوي مبسط وليس تقييمًا شاملًا للأمن السيبراني.",
        )
    )


# -----------------------------
# I Need Help
# -----------------------------
HELP_CONTENT = {
    "hacked": {
        "label_en": "My account may have been hacked",
        "label_ar": "قد يكون حسابي مخترقًا",
        "title_en": "Your Account May Have Been Hacked",
        "title_ar": "قد يكون حسابك قد تعرّض للاختراق",
        "intro_en": "Possible warning signs include login alerts you do not recognize, password changes you did not make, unknown messages sent from your account, or unfamiliar devices in your sessions.",
        "intro_ar": "من العلامات المحتملة: تنبيهات تسجيل دخول لا تعرفينها، تغيير كلمة المرور دون علمك، رسائل أُرسلت من حسابك دون أن ترسليها، أو أجهزة غير معروفة ضمن جلسات الحساب.",
        "steps_en": [
            "Change the password from the official app or website if you can still access the account.",
            "Use a strong, unique password that you do not use on another account.",
            "Sign out unfamiliar devices or active sessions.",
            "Check whether the recovery email or phone number was changed.",
            "Turn on two-factor authentication (2FA).",
            "Review recent account activity for changes you did not make.",
        ],
        "steps_ar": [
            "غيّري كلمة المرور من التطبيق أو الموقع الرسمي إذا كنت لا تزالين قادرة على الدخول إلى الحساب.",
            "استخدمي كلمة مرور قوية ومختلفة عن كلمات مرور حساباتك الأخرى.",
            "سجّلي الخروج من الأجهزة أو الجلسات غير المعروفة.",
            "تحققي من عدم تغيير بريد أو رقم استرداد الحساب.",
            "فعّلي المصادقة الثنائية (2FA).",
            "راجعي نشاط الحساب الأخير للتأكد من عدم وجود تغييرات لم تقومي بها.",
        ],
        "extra_title_en": "What if I can’t log in?",
        "extra_title_ar": "ماذا لو لم أستطع تسجيل الدخول؟",
        "extra_en": "Use the official account-recovery process. Be cautious of anyone who asks for money, passwords, or verification codes while claiming they can recover the account for you.",
        "extra_ar": "استخدمي طريقة استرداد الحساب الرسمية. واحذري من أي شخص يطلب مالًا أو كلمة مرور أو رمز تحقق مدعيًا أنه يستطيع استرداد الحساب لك.",
    },
    "impersonation": {
        "label_en": "Someone is impersonating me online",
        "label_ar": "شخص ينتحل شخصيتي على الإنترنت",
        "title_en": "Someone Is Impersonating You Online",
        "title_ar": "هناك شخص ينتحل شخصيتك على الإنترنت",
        "intro_en": "Impersonation means someone is using your name, photos, identity, or a similar account to make other people believe they are you.",
        "intro_ar": "انتحال الشخصية يعني أن شخصًا يستخدم اسمك أو صورك أو هويتك أو حسابًا مشابهًا ليجعل الآخرين يعتقدون أنه أنت.",
        "steps_en": [
            "Save evidence first: screenshots, the username, profile link, messages, and dates.",
            "Do not argue with the impersonator if that could escalate the situation.",
            "Report the fake account through the platform’s official reporting tools.",
            "Block the account after preserving the evidence you may need.",
            "Warn close contacts if the impersonator is messaging people you know.",
            "Review your privacy settings and reduce unnecessary public personal information.",
        ],
        "steps_ar": [
            "احفظي الأدلة أولًا: لقطات شاشة، اسم المستخدم، رابط الحساب، الرسائل والتواريخ.",
            "لا تدخلي في جدال مع المنتحل إذا كان ذلك قد يزيد المشكلة.",
            "أبلغي عن الحساب المزيف من خلال أدوات الإبلاغ الرسمية في المنصة.",
            "احظري الحساب بعد حفظ الأدلة التي قد تحتاجين إليها.",
            "نبّهي الأشخاص المقربين إذا كان المنتحل يراسل أشخاصًا تعرفينهم.",
            "راجعي إعدادات الخصوصية وقللي المعلومات الشخصية العامة غير الضرورية.",
        ],
        "extra_title_en": "What if the fake account already contacted people I know?",
        "extra_title_ar": "ماذا لو تواصل الحساب المزيف بالفعل مع أشخاص أعرفهم؟",
        "extra_en": "Tell your contacts which account is the real one and ask them not to send money, codes, private information, or files to the fake account.",
        "extra_ar": "أخبري معارفك بالحساب الحقيقي واطلبي منهم عدم إرسال مال أو رموز تحقق أو معلومات خاصة أو ملفات للحساب المزيف.",
    },
    "blackmail": {
        "label_en": "Someone is threatening or blackmailing me",
        "label_ar": "شخص يهددني أو يبتزني",
        "title_en": "Threats or Blackmail",
        "title_ar": "التهديد أو الابتزاز",
        "intro_en": "Digital blackmail happens when someone uses threats, private information, images, or fear to pressure you into sending money, more content, passwords, or doing something you do not want to do.",
        "intro_ar": "الابتزاز الرقمي يحدث عندما يستخدم شخص التهديد أو المعلومات أو الصور الخاصة أو الخوف للضغط عليك لإرسال المال أو المزيد من المحتوى أو كلمات المرور أو القيام بشيء لا تريدينه.",
        "steps_en": [
            "Do not send more private content, passwords, verification codes, or money because of the threat.",
            "Preserve evidence before deleting or blocking: screenshots, usernames, links, payment details, dates, and messages.",
            "Avoid prolonged arguments or bargaining with the person threatening you.",
            "Secure your accounts by changing compromised passwords and turning on 2FA.",
            "Report and block the account when it is safe to do so and after preserving evidence.",
            "Tell a trusted person and consider contacting an appropriate official or professional support service in your country.",
        ],
        "steps_ar": [
            "لا ترسلي المزيد من المحتوى الخاص أو كلمات المرور أو رموز التحقق أو المال بسبب التهديد.",
            "احفظي الأدلة قبل الحذف أو الحظر: لقطات الشاشة، أسماء المستخدمين، الروابط، تفاصيل الدفع، التواريخ والرسائل.",
            "تجنّبي الدخول في نقاش طويل أو مساومة مع الشخص الذي يهددك.",
            "أمّني حساباتك بتغيير كلمات المرور التي ربما انكشفت وتفعيل 2FA.",
            "أبلغي عن الحساب واحظريه عندما يكون ذلك آمنًا وبعد حفظ الأدلة.",
            "أخبري شخصًا موثوقًا وفكري في التواصل مع جهة رسمية أو مهنية مناسبة في بلدك.",
        ],
        "extra_title_en": "What if I already sent something?",
        "extra_title_ar": "ماذا لو كنت قد أرسلت شيئًا بالفعل؟",
        "extra_en": "Do not assume you must keep complying. Stop sending additional material, preserve evidence, secure your accounts, and seek trusted support. If you sent money, contact your bank or payment provider quickly. If there is immediate physical danger, contact the appropriate emergency service in your location.",
        "extra_ar": "لا تفترضي أنك مضطرة للاستمرار في الاستجابة لطلبات المبتز. توقفي عن إرسال أي مواد إضافية، واحفظي الأدلة، وأمّني حساباتك، واطلبي دعمًا موثوقًا. إذا أرسلت مالًا، تواصلي بسرعة مع البنك أو مزود الدفع. وإذا كان هناك خطر جسدي مباشر، تواصلي مع جهة الطوارئ المناسبة في مكانك.",
    },
    "harassment": {
        "label_en": "I am being harassed online",
        "label_ar": "أتعرّض للتحرش أو المضايقة عبر الإنترنت",
        "title_en": "Online Harassment",
        "title_ar": "التحرش والمضايقة عبر الإنترنت",
        "intro_en": "Online harassment can include repeated unwanted messages, insults, sexual comments, threats, stalking behavior, or attempts to intimidate you online.",
        "intro_ar": "قد يشمل التحرش عبر الإنترنت الرسائل المتكررة غير المرغوبة، الإهانات، التعليقات الجنسية، التهديدات، سلوك التتبع أو محاولات التخويف عبر الإنترنت.",
        "steps_en": [
            "Save evidence such as screenshots, usernames, links, and dates.",
            "Use block, mute, and report tools when appropriate.",
            "Review who can contact you, tag you, or view your posts and stories.",
            "Reduce unnecessary public details such as live location, phone number, routine, or address.",
            "Tell someone you trust if the harassment is persistent or upsetting.",
        ],
        "steps_ar": [
            "احفظي الأدلة مثل لقطات الشاشة وأسماء المستخدمين والروابط والتواريخ.",
            "استخدمي أدوات الحظر والكتم والإبلاغ عندما يكون ذلك مناسبًا.",
            "راجعي من يستطيع التواصل معك أو الإشارة إليك أو رؤية منشوراتك وقصصك.",
            "قللي نشر التفاصيل غير الضرورية مثل الموقع المباشر أو رقم الهاتف أو الروتين أو العنوان.",
            "أخبري شخصًا تثقين به إذا كانت المضايقة مستمرة أو مزعجة.",
        ],
        "extra_title_en": "What if the harassment keeps happening or becomes threatening?",
        "extra_title_ar": "ماذا لو استمرت المضايقة أو أصبحت تهديدًا؟",
        "extra_en": "If the harassment continues after blocking, moves to new accounts, includes threats, exposes private information, tracks your location, or creates a real-world safety concern, preserve the evidence and seek trusted or appropriate official support.",
        "extra_ar": "إذا استمرت المضايقة بعد الحظر، أو انتقلت إلى حسابات جديدة، أو تضمنت تهديدات، أو كشف معلومات خاصة، أو تتبع موقعك، أو سببت خوفًا على سلامتك خارج الإنترنت، فاحفظي الأدلة واطلبي دعمًا موثوقًا أو رسميًا مناسبًا.",
    },
    "link": {
        "label_en": "I received a suspicious link",
        "label_ar": "وصلني رابط مشبوه",
        "title_en": "Suspicious Link",
        "title_ar": "رابط مشبوه",
        "intro_en": "A suspicious link may lead to a fake login page, a malicious download, or a site designed to steal account, payment, or personal information.",
        "intro_ar": "قد يقود الرابط المشبوه إلى صفحة تسجيل دخول مزيفة أو ملف ضار أو موقع مصمم لسرقة بيانات الحساب أو الدفع أو المعلومات الشخصية.",
        "steps_en": [
            "If you have NOT opened it, do not click the link.",
            "Verify the message through the official app, website, or a trusted contact method.",
            "Do not enter passwords, verification codes, or payment details on a page reached through an unexpected link.",
            "If the link came from someone you know, confirm with them through another channel because their account may have been compromised.",
        ],
        "steps_ar": [
            "إذا لم تكوني قد فتحته، فلا تضغطي على الرابط.",
            "تحققي من الرسالة من خلال التطبيق أو الموقع الرسمي أو وسيلة تواصل موثوقة.",
            "لا تدخلي كلمات المرور أو رموز التحقق أو معلومات الدفع في صفحة وصلتِ إليها من رابط غير متوقع.",
            "إذا أرسل الرابط شخص تعرفينه، فتأكدي منه عبر وسيلة أخرى لأن حسابه قد يكون مخترقًا.",
        ],
        "extra_title_en": "What if I already clicked the link?",
        "extra_title_ar": "ماذا لو ضغطت على الرابط بالفعل؟",
        "extra_en": "If you only opened the page and entered nothing, close it and avoid downloading unexpected files. If you entered a password, open the official app or website directly, change the password, enable 2FA, and review active sessions. If you entered payment information, contact your bank or payment provider quickly. If you downloaded a file, do not open an unexpected file and use a trusted security scan.",
        "extra_ar": "إذا فتحتِ الصفحة فقط ولم تدخلي شيئًا، فأغلقيها وتجنبي تنزيل الملفات غير المتوقعة. إذا أدخلتِ كلمة مرور، افتحي التطبيق أو الموقع الرسمي مباشرة، وغيّري كلمة المرور، وفعّلي 2FA، وراجعي جلسات الدخول. إذا أدخلتِ معلومات دفع، فتواصلي بسرعة مع البنك أو مزود الدفع. وإذا نزّلتِ ملفًا، فلا تفتحي ملفًا غير متوقع واستخدمي فحص أمان موثوقًا.",
    },
}


def render_help():
    back_home()
    st.title(tr("🛡️ I Need Help", "🛡️ أحتاج مساعدة"))
    st.write(
        tr(
            "Choose the situation that best matches what happened. You do not need to enter private details.",
            "اختاري الحالة الأقرب لما حدث. لا تحتاجين إلى إدخال تفاصيل شخصية أو خاصة.",
        )
    )

    soft_card(
        tr(
            "🧭 Your response path: Respond Now → Prepare My Report → Get Official Help",
            "🧭 مسار المساعدة: تصرّفي الآن ← جهّزي بلاغك ← احصلي على مساعدة رسمية",
        ),
        "neutral",
        margin_top=8,
        margin_bottom=18,
    )

    situation_keys = list(HELP_CONTENT.keys())
    selected_key = st.selectbox(
        tr("What happened?", "ما الذي حدث؟"),
        situation_keys,
        format_func=lambda key: tr(HELP_CONTENT[key]["label_en"], HELP_CONTENT[key]["label_ar"]),
        key="help_situation",
    )

    item = HELP_CONTENT[selected_key]
    st.markdown(f"## {tr(item['title_en'], item['title_ar'])}")
    st.write(tr(item["intro_en"], item["intro_ar"]))

    # ---------------------------------------------------------
    # 1. RESPOND NOW
    # ---------------------------------------------------------
    st.markdown(tr("### 🛡️ 1. Respond Now", "### 🛡️ 1. تصرّفي الآن"))
    st.caption(
        tr(
            "Start with these immediate steps before moving to reporting.",
            "ابدئي بهذه الخطوات الفورية قبل الانتقال إلى إعداد البلاغ.",
        )
    )

    steps = item["steps_ar"] if LANG == "AR" else item["steps_en"]
    for number, step in enumerate(steps, start=1):
        st.write(f"{number}. {step}")

    # Warm, situation-specific What-if cards for every help topic.
    if selected_key == "hacked":
        st.markdown(f"### ❓ {tr(item['extra_title_en'], item['extra_title_ar'])}")
        soft_card(
            tr(
                "Use the platform’s official account-recovery process from the real app or website. Check your email for security notices about password, recovery-email, or phone-number changes.",
                "استخدمي طريقة استرداد الحساب الرسمية من التطبيق أو الموقع الحقيقي للمنصة. وراجعي بريدك الإلكتروني بحثًا عن تنبيهات أمان حول تغيير كلمة المرور أو بريد الاسترداد أو رقم الهاتف.",
            ),
            "info",
        )
        soft_card(
            tr(
                "Be careful with anyone who asks for money, passwords, or verification codes while claiming they can recover the account for you.",
                "احذري من أي شخص يطلب مالًا أو كلمة مرور أو رمز تحقق مدعيًا أنه يستطيع استرداد الحساب لك.",
            ),
            "warning",
            margin_top=5,
            margin_bottom=18,
        )

    elif selected_key == "impersonation":
        st.markdown(f"### ❓ {tr(item['extra_title_en'], item['extra_title_ar'])}")
        soft_card(
            tr(
                "Tell your contacts which account is the real one and ask them not to send money, verification codes, private information, or files to the fake account.",
                "أخبري معارفك أي حساب هو حسابك الحقيقي، واطلبي منهم عدم إرسال مال أو رموز تحقق أو معلومات خاصة أو ملفات للحساب المزيف.",
            ),
            "info",
        )
        soft_card(
            tr(
                "Keep screenshots of the fake profile and any messages it sent before the account disappears or changes its username.",
                "احتفظي بلقطات شاشة للحساب المزيف وأي رسائل أرسلها قبل أن يختفي الحساب أو يغيّر اسم المستخدم.",
            ),
            "warning",
            margin_top=5,
            margin_bottom=18,
        )

    elif selected_key == "blackmail":
        soft_card(
            tr(
                "Paying or sending more private content does not guarantee that the threats will stop.",
                "دفع المال أو إرسال المزيد من المحتوى الخاص لا يضمن أن التهديدات ستتوقف.",
            ),
            "warning",
            margin_top=18,
            margin_bottom=18,
        )

        st.markdown(f"### ❓ {tr(item['extra_title_en'], item['extra_title_ar'])}")
        soft_card(
            tr(
                "Do not keep sending more because of new demands. Preserve the evidence and secure any accounts involved. If you transferred money, contact the bank or payment provider as soon as possible.",
                "لا تستمري في إرسال المزيد بسبب طلبات جديدة. احفظي الأدلة وأمّني أي حسابات مرتبطة بالموقف. وإذا حوّلتِ مالًا، تواصلي مع البنك أو مزود خدمة الدفع بأسرع وقت ممكن.",
            ),
            "info",
        )
        soft_card(
            tr(
                "If you believe you are in immediate physical danger, prioritize your personal safety and seek appropriate local help.",
                "إذا كنت تعتقدين أن هناك خطرًا جسديًا مباشرًا، فاجعلي سلامتك الشخصية أولوية واطلبي المساعدة المحلية المناسبة.",
            ),
            "danger",
            margin_top=5,
            margin_bottom=18,
        )

    elif selected_key == "harassment":
        st.markdown(f"### ❓ {tr(item['extra_title_en'], item['extra_title_ar'])}")
        soft_card(tr(item["extra_en"], item["extra_ar"]), "warning")
        soft_card(
            tr(
                "If the situation creates an immediate real-world safety concern, prioritize your physical safety and seek appropriate local help.",
                "إذا أصبح الموقف يسبب خطرًا مباشرًا على سلامتك خارج الإنترنت، فاجعلي سلامتك الجسدية أولوية واطلبي المساعدة المحلية المناسبة.",
            ),
            "danger",
            margin_top=5,
            margin_bottom=18,
        )

    elif selected_key == "link":
        st.markdown(f"### ❓ {tr(item['extra_title_en'], item['extra_title_ar'])}")
        soft_card(
            tr(
                "If you only opened the page and entered nothing, close it and avoid downloading unexpected files. If you entered a password, go directly to the official app or website, change it, enable 2FA, and review active sessions.",
                "إذا فتحتِ الصفحة فقط ولم تدخلي شيئًا، فأغلقيها وتجنبي تنزيل الملفات غير المتوقعة. وإذا أدخلتِ كلمة مرور، فانتقلي مباشرة إلى التطبيق أو الموقع الرسمي، وغيّريها، وفعّلي 2FA، وراجعي جلسات الدخول.",
            ),
            "info",
        )
        soft_card(
            tr(
                "If you entered payment information, contact your bank or payment provider quickly. If you downloaded a file, do not open an unexpected file and use a trusted security scan.",
                "إذا أدخلتِ معلومات دفع، فتواصلي بسرعة مع البنك أو مزود الدفع. وإذا نزّلتِ ملفًا، فلا تفتحي ملفًا غير متوقع واستخدمي فحص أمان موثوقًا.",
            ),
            "warning",
            margin_top=5,
            margin_bottom=18,
        )

    st.divider()

    # ---------------------------------------------------------
    # 2. PREPARE MY REPORT
    # ---------------------------------------------------------
    st.markdown(tr("### 📝 2. Prepare My Report", "### 📝 2. جهّزي بلاغك"))

    soft_card(
        tr(
            "HISNHA can organize the basic facts into a clear report draft. This step does not call Gemini and does not submit anything automatically.",
            "تستطيع حِصنها ترتيب المعلومات الأساسية في مسودة بلاغ واضحة. هذه الخطوة لا تستخدم Gemini ولا ترسل أي شيء تلقائيًا.",
        ),
        "info",
        margin_top=6,
        margin_bottom=10,
    )

    st.caption(
        tr(
            "⚠️ Do not enter passwords, OTP codes, banking credentials, private images, or other highly sensitive information.",
            "⚠️ لا تُدخلي كلمات المرور أو رموز OTP أو بيانات الدخول البنكية أو الصور الخاصة أو أي معلومات شديدة الحساسية.",
        )
    )

    if LANG == "AR":
        evidence_options = [
            "لقطات شاشة",
            "رسائل أو محادثات",
            "اسم مستخدم أو رابط حساب",
            "رابط أو موقع إلكتروني",
            "تفاصيل تحويل أو دفع",
            "تنبيهات أمان أو تسجيل دخول",
            "أدلة أخرى",
        ]
        impact_options = [
            "ضغطت على رابط",
            "شاركت معلومات حساب",
            "شاركت كلمة مرور أو رمز تحقق",
            "أرسلت مالًا أو معلومات دفع",
            "فقدت الوصول إلى حساب",
            "تم نشر أو التهديد بنشر معلومات/محتوى خاص",
            "تلقيت تهديدًا مباشرًا",
            "لا شيء مما سبق / غير متأكدة",
        ]
        danger_options = ["لا", "غير متأكدة", "نعم"]
    else:
        evidence_options = [
            "Screenshots",
            "Messages or chat history",
            "Username or profile link",
            "Website or URL",
            "Payment or transfer details",
            "Security/login alerts",
            "Other evidence",
        ]
        impact_options = [
            "I clicked a link",
            "I shared account information",
            "I shared a password or verification code",
            "I sent money or payment information",
            "I lost access to an account",
            "Private information/content was shared or threatened",
            "I received a direct threat",
            "None of these / I am not sure",
        ]
        danger_options = ["No", "Not sure", "Yes"]

    with st.form(key=f"report_form_{selected_key}"):
        platform = st.text_input(
            tr("Platform or service *", "المنصة أو الخدمة *"),
            placeholder=tr("e.g., Instagram, WhatsApp, Email", "مثال: Instagram أو WhatsApp أو البريد الإلكتروني"),
        )

        incident_time = st.text_input(
            tr("When did it happen? (optional)", "متى حدث ذلك؟ (اختياري)"),
            placeholder=tr("e.g., 26 Aug 2026, around 3 PM", "مثال: 26 أغسطس 2026، حوالي الساعة 3 مساءً"),
        )

        account_reference = st.text_input(
            tr("Account, username, or link involved (optional)", "الحساب أو اسم المستخدم أو الرابط المرتبط بالحادثة (اختياري)"),
            placeholder=tr("@username or profile/link", "@username أو رابط الحساب"),
        )

        short_summary = st.text_area(
            tr("Brief factual description *", "وصف مختصر وواقعي لما حدث *"),
            height=120,
            placeholder=tr(
                "Describe what happened in a few sentences without adding passwords, codes, or private images.",
                "صفي ما حدث بعدة جمل بدون إضافة كلمات مرور أو رموز تحقق أو صور خاصة.",
            ),
        )

        evidence = st.multiselect(
            tr("Evidence you have", "الأدلة المتوفرة لديك"),
            evidence_options,
        )

        impact = st.multiselect(
            tr("What has already happened?", "ما الذي حدث بالفعل؟"),
            impact_options,
        )

        immediate_danger = st.radio(
            tr(
                "Is there an immediate concern for your physical safety?",
                "هل يوجد خطر مباشر على سلامتك الجسدية؟",
            ),
            danger_options,
            horizontal=True,
            index=0,
        )

        prepare_clicked = st.form_submit_button(
            tr("📝 Prepare Report Draft", "📝 تجهيز مسودة البلاغ"),
            type="primary",
            use_container_width=True,
        )

    report_key = f"prepared_report_{selected_key}"
    editable_report_key = f"editable_report_{selected_key}"

    if prepare_clicked:
        if not platform.strip() or not short_summary.strip():
            st.warning(
                tr(
                    "Please complete the platform/service and brief description first.",
                    "يرجى تعبئة المنصة أو الخدمة والوصف المختصر أولًا.",
                )
            )
        else:
            evidence_text = ", ".join(evidence) if evidence else tr("Not specified", "غير محدد")
            impact_text = ", ".join(impact) if impact else tr("Not specified", "غير محدد")
            time_text = incident_time.strip() if incident_time.strip() else tr("Not specified", "غير محدد")
            reference_text = account_reference.strip() if account_reference.strip() else tr("Not specified", "غير محدد")

            if LANG == "AR":
                report_text = (
                    "مسودة بلاغ عن حادثة رقمية – حِصنها\n"
                    "----------------------------------\n"
                    f"نوع الحادثة: {item['label_ar']}\n"
                    f"المنصة أو الخدمة: {platform.strip()}\n"
                    f"وقت/تاريخ الحادثة: {time_text}\n"
                    f"الحساب/اسم المستخدم/الرابط: {reference_text}\n\n"
                    f"وصف مختصر:\n{short_summary.strip()}\n\n"
                    f"الأدلة المتوفرة: {evidence_text}\n"
                    f"ما الذي حدث بالفعل: {impact_text}\n"
                    f"خطر مباشر على السلامة الجسدية: {immediate_danger}\n\n"
                    "ملاحظة: تمت صياغة هذه المسودة بواسطة حِصنها لمساعدة المستخدمة على تنظيم المعلومات. "
                    "راجعيها قبل إرسالها إلى أي جهة رسمية."
                )
            else:
                report_text = (
                    "Digital Incident Report Draft – HISNHA\n"
                    "--------------------------------------\n"
                    f"Incident type: {item['label_en']}\n"
                    f"Platform or service: {platform.strip()}\n"
                    f"Date/time: {time_text}\n"
                    f"Account/username/link: {reference_text}\n\n"
                    f"Brief description:\n{short_summary.strip()}\n\n"
                    f"Evidence available: {evidence_text}\n"
                    f"What has already happened: {impact_text}\n"
                    f"Immediate physical-safety concern: {immediate_danger}\n\n"
                    "Note: This draft was formatted by HISNHA to help the user organize the basic facts. "
                    "Review it before sending it to any official authority."
                )

            st.session_state[report_key] = report_text
            st.session_state[editable_report_key] = report_text

    prepared_report = st.session_state.get(report_key)

    if prepared_report:
        st.success(
            tr(
                "Your report draft is ready. Review or edit it before contacting an official authority.",
                "مسودة البلاغ جاهزة. راجعيها أو عدّليها قبل التواصل مع أي جهة رسمية.",
            )
        )

        edited_report = st.text_area(
            tr("Report preview — you can edit it", "معاينة البلاغ — يمكنك تعديله"),
            key=editable_report_key,
            height=300,
        )

        st.download_button(
            tr("⬇️ Save Report as TXT", "⬇️ حفظ البلاغ كملف TXT"),
            data=edited_report,
            file_name="HISNHA_incident_report.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        edited_report = ""

    st.divider()

    # ---------------------------------------------------------
    # 3. GET OFFICIAL HELP — JORDAN
    # ---------------------------------------------------------
    st.markdown(tr("### 🏛️ 3. Get Official Help", "### 🏛️ 3. احصلي على مساعدة رسمية"))

    soft_card(
        tr(
            "Official support in this prototype is currently configured for Jordan. HISNHA opens the official contact channel; it does not submit a report on your behalf.",
            "الدعم الرسمي في هذا النموذج الأولي مهيأ حاليًا للأردن. تفتح حِصنها قناة التواصل الرسمية، لكنها لا ترسل البلاغ نيابةً عنك.",
        ),
        "neutral",
        margin_top=6,
        margin_bottom=14,
    )

    st.markdown(
        tr(
            "**Jordan Public Security Directorate — Cybercrime Unit**",
            "**مديرية الأمن العام الأردنية — وحدة مكافحة الجرائم الإلكترونية**",
        )
    )

    st.write(
        tr(
            "Phone: **196** — extensions **812594 / 812232**",
            "الهاتف: **196** — الفرعي **812594 / 812232**",
        )
    )
    st.write("Email: **ecrimes@psd.gov.jo**")

    cybercrime_page = (
        "https://www.psd.gov.jo/ar-jo/"
        "%D8%A7%D9%84%D8%A5%D8%AF%D8%A7%D8%B1%D8%A7%D8%AA-%D9%88%D8%A7%D9%84%D9%88%D8%AD%D8%AF%D8%A7%D8%AA/"
        "%D8%A5%D8%AF%D8%A7%D8%B1%D8%A9-%D8%A7%D9%84%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%AC%D9%86%D8%A7%D8%A6%D9%8A/"
        "%D9%88%D8%AD%D8%AF%D8%A9-%D9%85%D9%83%D8%A7%D9%81%D8%AD%D8%A9-%D8%A7%D9%84%D8%AC%D8%B1%D8%A7%D8%A6%D9%85-"
        "%D8%A7%D9%84%D8%A5%D9%84%D9%83%D8%AA%D8%B1%D9%88%D9%86%D9%8A%D8%A9/"
    )

    email_subject = tr(
        "Cybercrime Incident Report",
        "بلاغ عن حادثة إلكترونية",
    )

    email_body = edited_report.strip() if edited_report.strip() else tr(
        "I would like to report a cybercrime incident. I will provide the relevant facts and evidence through the appropriate official process.",
        "أرغب في الإبلاغ عن حادثة إلكترونية، وسأقدّم المعلومات والأدلة ذات الصلة من خلال الإجراء الرسمي المناسب.",
    )

    mailto_url = (
        "mailto:ecrimes@psd.gov.jo"
        f"?subject={quote(email_subject)}"
        f"&body={quote(email_body)}"
    )

    # Email and official-page access are safe to expose directly.
    contact_col1, contact_col2 = st.columns(2)

    with contact_col1:
        st.link_button(
            tr("✉️ Email Cybercrime Unit", "✉️ مراسلة وحدة الجرائم الإلكترونية"),
            mailto_url,
            use_container_width=True,
        )

    with contact_col2:
        st.link_button(
            tr("🌐 Open Official Page", "🌐 فتح الصفحة الرسمية"),
            cybercrime_page,
            use_container_width=True,
        )

    st.caption(
        tr(
            "The email button only opens your email app with a draft. Nothing is sent until you review it and press Send.",
            "زر البريد يفتح تطبيق البريد مع مسودة جاهزة فقط. لن يتم إرسال أي شيء قبل أن تراجعيه وتضغطي إرسال.",
        )
    )

    # Final-production safety: phone actions are shown only after an explicit user confirmation.
    allow_call_links = st.checkbox(
        tr(
            "I want to open official phone-contact options.",
            "أرغب في إظهار خيارات الاتصال الهاتفي الرسمية.",
        ),
        key=f"allow_official_calls_{selected_key}",
    )

    if allow_call_links:
        soft_card(
            tr(
                "📞 These buttons open your phone's calling screen with the official number. HISNHA does not place the call automatically.",
                "📞 هذه الأزرار تفتح شاشة الاتصال في هاتفك على الرقم الرسمي. حِصنها لا تجري المكالمة تلقائيًا.",
            ),
            "info",
            margin_top=6,
            margin_bottom=10,
        )

        st.link_button(
            tr("📞 Open Call Screen — Cybercrime Unit (196)", "📞 فتح شاشة الاتصال — وحدة الجرائم الإلكترونية (196)"),
            "tel:196",
            use_container_width=True,
        )

    # Keep HISNHA focused on digital-safety support.
    # If the user reports immediate physical danger, provide general emergency guidance
    # without embedding or dialing an emergency number inside the app.
    danger_is_yes = immediate_danger in ("Yes", "نعم")

    if danger_is_yes:
        soft_card(
            tr(
                "🚨 If you are in immediate physical danger, prioritize your personal safety and contact the appropriate local emergency services or a trusted person who can help you reach safety.",
                "🚨 إذا كنتِ في خطر جسدي مباشر، فاجعلي سلامتك الشخصية أولوية وتواصلي مع خدمات الطوارئ المحلية المناسبة أو مع شخص موثوق يمكنه مساعدتك للوصول إلى مكان آمن.",
            ),
            "danger",
            margin_top=14,
            margin_bottom=8,
        )

    st.divider()

    soft_card(
        tr(
            "💜 HISNHA provides general digital-safety guidance. You do not need to share sensitive details to use this section.",
            "💜 تقدّم حِصنها إرشادات عامة للسلامة الرقمية. لا تحتاجين إلى مشاركة تفاصيل حساسة للاستفادة من هذا القسم.",
        ),
        "remember",
        margin_top=8,
        margin_bottom=10,
    )

    st.caption(
        tr(
            "HISNHA does not replace legal, emergency, financial, or professional support when those services are needed.",
            "لا تستبدل حِصنها الدعم القانوني أو الطارئ أو المالي أو المهني عندما تكون هذه الخدمات مطلوبة.",
        )
    )

# -----------------------------
# Learn
# -----------------------------
LESSONS = {
    "phishing": {
        "label_en": "🎣 Phishing",
        "label_ar": "🎣 التصيد الإلكتروني",
        "title_en": "Phishing",
        "title_ar": "التصيد الإلكتروني",
        "what_en": "Phishing is a scam where someone pretends to be a trusted person or service to make you reveal information, click a dangerous link, or take an unsafe action.",
        "what_ar": "التصيد الإلكتروني هو أسلوب احتيالي ينتحل فيه شخص صفة جهة أو شخص موثوق لدفعك إلى كشف معلومات، أو فتح رابط خطير، أو القيام بتصرف غير آمن.",
        "example_en": "A message says your account will be closed today unless you open a link and confirm your password.",
        "example_ar": "رسالة تقول إن حسابك سيُغلق اليوم ما لم تفتحي رابطًا وتؤكدي كلمة المرور.",
        "danger_en": "A fake page can steal your password, verification code, payment details, or other personal information.",
        "danger_ar": "قد تسرق الصفحة المزيفة كلمة المرور أو رمز التحقق أو معلومات الدفع أو بيانات شخصية أخرى.",
        "signs_en": ["Unexpected urgency or threats", "A link you were not expecting", "Requests for passwords or verification codes", "A sender name that looks familiar but the account or address is unusual"],
        "signs_ar": ["استعجال أو تهديد غير متوقع", "رابط لم تكوني تتوقعينه", "طلب كلمة مرور أو رمز تحقق", "اسم مرسل مألوف لكن الحساب أو العنوان غير معتاد"],
        "actions_en": ["Do not use the link in the message.", "Open the official app or website directly.", "Verify the request through a trusted channel.", "Never send your password or verification code to another person."],
        "actions_ar": ["لا تستخدمي الرابط الموجود في الرسالة.", "افتحي التطبيق أو الموقع الرسمي مباشرة.", "تحققي من الطلب عبر وسيلة موثوقة.", "لا ترسلي كلمة المرور أو رمز التحقق لأي شخص."],
        "word_en": "Phishing = a social-engineering attack designed to trick a person into giving information or taking an unsafe action.",
        "word_ar": "Phishing (التصيد الإلكتروني) = هجوم هندسة اجتماعية يهدف إلى خداع الشخص لكشف معلومات أو القيام بتصرف غير آمن.",
        "video": "JlQovysQBn0",
        "caption_en": "CISA guidance on recognizing and reporting phishing.",
        "caption_ar": "إرشادات من CISA حول التعرّف على التصيد والإبلاغ عنه.",
        "resource": "https://www.cisa.gov/secure-our-world/recognize-and-report-phishing",
        "resource_name": "CISA",
        "quiz_q_en": "Which action is safest after receiving an unexpected account-warning link?",
        "quiz_q_ar": "ما التصرف الأكثر أمانًا بعد استلام رابط غير متوقع يحذرك من مشكلة في الحساب؟",
        "quiz_options_en": ["Open the link quickly", "Open the official app or website directly", "Send your password to confirm your identity"],
        "quiz_options_ar": ["فتح الرابط بسرعة", "فتح التطبيق أو الموقع الرسمي مباشرة", "إرسال كلمة المرور لتأكيد الهوية"],
        "correct": 1,
    },
    "passwords": {
        "label_en": "🔑 Strong Passwords",
        "label_ar": "🔑 كلمات المرور القوية",
        "title_en": "Strong Passwords",
        "title_ar": "كلمات المرور القوية",
        "what_en": "A strong password is difficult for another person or automated tool to guess and is not reused across important accounts.",
        "what_ar": "كلمة المرور القوية يصعب على شخص أو أداة آلية تخمينها، ولا يتم إعادة استخدامها على الحسابات المهمة.",
        "example_en": "Using the same password for email, social media, and shopping means one password leak could expose several accounts.",
        "example_ar": "استخدام كلمة المرور نفسها للبريد والتواصل الاجتماعي والتسوق يعني أن تسريب كلمة واحدة قد يعرّض عدة حسابات للخطر.",
        "danger_en": "Password reuse can turn one breach into access to several of your accounts.",
        "danger_ar": "إعادة استخدام كلمة المرور قد تجعل اختراق خدمة واحدة يؤدي إلى الوصول لعدة حسابات لديك.",
        "signs_en": ["You reuse the same password", "Your password contains obvious personal information", "Your password is short or easy to guess"],
        "signs_ar": ["تستخدمين كلمة المرور نفسها في أكثر من مكان", "تحتوي كلمة المرور على معلومات شخصية واضحة", "كلمة المرور قصيرة أو سهلة التخمين"],
        "actions_en": ["Use a unique password for each important account.", "Prefer long passwords or passphrases.", "Use a trusted password manager if it is suitable for you.", "Change passwords that were exposed in a breach."],
        "actions_ar": ["استخدمي كلمة مرور مختلفة لكل حساب مهم.", "فضّلي كلمات المرور الطويلة أو العبارات السرية.", "استخدمي مدير كلمات مرور موثوقًا إذا كان مناسبًا لك.", "غيّري كلمات المرور التي تبيّن أنها تسرّبت."],
        "word_en": "Password manager = a tool designed to securely store and help generate passwords.",
        "word_ar": "Password Manager (مدير كلمات المرور) = أداة مصممة لحفظ كلمات المرور بشكل آمن والمساعدة في إنشاء كلمات قوية.",
        "video": "FZoB7yUGh7Y",
        "caption_en": "CISA guidance on using strong passwords.",
        "caption_ar": "إرشادات من CISA حول استخدام كلمات مرور قوية.",
        "resource": "https://www.cisa.gov/secure-our-world/use-strong-passwords",
        "resource_name": "CISA",
        "quiz_q_en": "Which password habit is safer?",
        "quiz_q_ar": "أي عادة لكلمات المرور أكثر أمانًا؟",
        "quiz_options_en": ["Reuse one strong password everywhere", "Use a different strong password for each important account", "Use your birthday because it is easy to remember"],
        "quiz_options_ar": ["استخدام كلمة مرور قوية واحدة في كل مكان", "استخدام كلمة مرور قوية ومختلفة لكل حساب مهم", "استخدام تاريخ الميلاد لأنه سهل التذكر"],
        "correct": 1,
    },
    "2fa": {
        "label_en": "🔐 Two-Factor Authentication",
        "label_ar": "🔐 المصادقة الثنائية",
        "title_en": "Two-Factor Authentication (2FA)",
        "title_ar": "المصادقة الثنائية (2FA)",
        "what_en": "Two-factor authentication adds another verification step in addition to your password.",
        "what_ar": "المصادقة الثنائية تضيف خطوة تحقق أخرى إلى جانب كلمة المرور.",
        "example_en": "After entering your password, the service asks for a code from an authenticator app or another approved verification method.",
        "example_ar": "بعد إدخال كلمة المرور، تطلب الخدمة رمزًا من تطبيق مصادقة أو وسيلة تحقق أخرى معتمدة.",
        "danger_en": "Without an additional factor, a stolen password may be enough for an attacker to access the account.",
        "danger_ar": "بدون عامل تحقق إضافي، قد تكون كلمة المرور المسروقة وحدها كافية للوصول إلى الحساب.",
        "signs_en": ["Important accounts only depend on a password", "You approve login requests you did not start", "Someone asks you to send them a verification code"],
        "signs_ar": ["الحسابات المهمة تعتمد فقط على كلمة المرور", "توافقين على طلبات دخول لم تبدئيها", "شخص يطلب منك إرسال رمز تحقق"],
        "actions_en": ["Enable 2FA on important accounts.", "Prefer secure authenticator methods when available.", "Never share a verification code with another person.", "Reject login approvals you did not request."],
        "actions_ar": ["فعّلي 2FA على الحسابات المهمة.", "فضّلي وسائل المصادقة الآمنة عندما تكون متاحة.", "لا تشاركي رمز التحقق مع أي شخص.", "ارفُضي طلبات الموافقة على تسجيل الدخول التي لم تطلبيها."],
        "word_en": "2FA = Two-Factor Authentication, a second verification layer beyond the password.",
        "word_ar": "2FA = المصادقة الثنائية، وهي طبقة تحقق إضافية إلى جانب كلمة المرور.",
        "video": "XIlF2qkav5c",
        "caption_en": "CISA guidance on turning on multi-factor authentication.",
        "caption_ar": "إرشادات من CISA حول تفعيل المصادقة متعددة العوامل.",
        "resource": "https://www.cisa.gov/secure-our-world/turn-mfa",
        "resource_name": "CISA",
        "quiz_q_en": "What should you do if someone asks you to send them the verification code you just received?",
        "quiz_q_ar": "ماذا تفعلين إذا طلب منك شخص إرسال رمز التحقق الذي وصلك للتو؟",
        "quiz_options_en": ["Send it if they sound urgent", "Never share it with another person", "Post it in a group to ask if it is safe"],
        "quiz_options_ar": ["إرساله إذا كان الطلب مستعجلًا", "عدم مشاركته مع أي شخص", "نشره في مجموعة للسؤال إذا كان آمنًا"],
        "correct": 1,
    },
    "impersonation": {
        "label_en": "👤 Fake Accounts & Impersonation",
        "label_ar": "👤 الحسابات المزيفة وانتحال الشخصية",
        "title_en": "Fake Accounts & Impersonation",
        "title_ar": "الحسابات المزيفة وانتحال الشخصية",
        "what_en": "Impersonation happens when someone pretends to be another person or organization to gain trust, deceive others, or cause harm.",
        "what_ar": "يحدث انتحال الشخصية عندما يتظاهر شخص بأنه شخص أو جهة أخرى لكسب الثقة أو خداع الآخرين أو إحداث ضرر.",
        "example_en": "A new account uses your friend’s photo and asks you for money, a code, or private information.",
        "example_ar": "حساب جديد يستخدم صورة صديقتك ويطلب منك مالًا أو رمز تحقق أو معلومات خاصة.",
        "danger_en": "A fake identity can be used for scams, reputation harm, privacy violations, or account theft.",
        "danger_ar": "قد تُستخدم الهوية المزيفة في الاحتيال أو الإضرار بالسمعة أو انتهاك الخصوصية أو سرقة الحسابات.",
        "signs_en": ["A slightly different username", "A new account with little history", "Unexpected requests for money or codes", "The person refuses normal verification"],
        "signs_ar": ["اسم مستخدم مختلف قليلًا", "حساب جديد بسجل نشاط محدود", "طلبات غير متوقعة للمال أو الرموز", "رفض الشخص التحقق بطريقة طبيعية"],
        "actions_en": ["Verify through a second trusted channel.", "Do not send money, passwords, or verification codes.", "Save evidence and report fake accounts.", "Warn contacts if your identity is being copied."],
        "actions_ar": ["تحققي عبر وسيلة موثوقة ثانية.", "لا ترسلي مالًا أو كلمات مرور أو رموز تحقق.", "احفظي الأدلة وأبلغي عن الحسابات المزيفة.", "نبّهي معارفك إذا تم نسخ هويتك."],
        "word_en": "Impersonation = pretending to be another person or entity in order to deceive others.",
        "word_ar": "Impersonation (انتحال الشخصية) = التظاهر بأنك شخص أو جهة أخرى بهدف خداع الآخرين.",
        "video": "-89h8FGgypQ",
        "caption_en": "FTC guidance on avoiding imposter scams.",
        "caption_ar": "إرشادات من FTC حول تجنب عمليات الاحتيال بانتحال الهوية.",
        "resource": "https://consumer.ftc.gov/features/how-avoid-imposter-scams",
        "resource_name": "FTC",
        "quiz_q_en": "A new account using your friend’s photo asks for money. What should you do first?",
        "quiz_q_ar": "حساب جديد يستخدم صورة صديقتك ويطلب مالًا. ما أول شيء يجب فعله؟",
        "quiz_options_en": ["Send a small amount", "Verify with your friend through another trusted channel", "Send your own account details"],
        "quiz_options_ar": ["إرسال مبلغ صغير", "التحقق من صديقتك عبر وسيلة موثوقة أخرى", "إرسال تفاصيل حسابك أنت"],
        "correct": 1,
    },
    "harassment": {
        "label_en": "💬 Online Harassment",
        "label_ar": "💬 التحرش والمضايقة عبر الإنترنت",
        "title_en": "Online Harassment",
        "title_ar": "التحرش والمضايقة عبر الإنترنت",
        "what_en": "Online harassment is repeated or harmful digital behavior intended to intimidate, humiliate, threaten, or distress another person.",
        "what_ar": "التحرش عبر الإنترنت هو سلوك رقمي متكرر أو مؤذٍ يهدف إلى تخويف شخص أو إذلاله أو تهديده أو إزعاجه.",
        "example_en": "Someone repeatedly sends unwanted sexual comments and creates new accounts after being blocked.",
        "example_ar": "شخص يرسل تعليقات جنسية غير مرغوبة بشكل متكرر وينشئ حسابات جديدة بعد حظره.",
        "danger_en": "Harassment can affect privacy, emotional wellbeing, reputation, and in some cases real-world safety.",
        "danger_ar": "قد يؤثر التحرش على الخصوصية والراحة النفسية والسمعة، وفي بعض الحالات على السلامة في الحياة الواقعية.",
        "signs_en": ["Repeated unwanted contact", "Threats or intimidation", "Sexual or degrading comments", "Attempts to expose private information or track you"],
        "signs_ar": ["تواصل متكرر غير مرغوب", "تهديد أو تخويف", "تعليقات جنسية أو مهينة", "محاولات لكشف معلوماتك الخاصة أو تتبعك"],
        "actions_en": ["Preserve evidence.", "Use block, mute, and report tools.", "Review privacy settings.", "Tell a trusted person if the behavior continues or escalates."],
        "actions_ar": ["احفظي الأدلة.", "استخدمي الحظر والكتم والإبلاغ.", "راجعي إعدادات الخصوصية.", "أخبري شخصًا تثقين به إذا استمر السلوك أو تصاعد."],
        "word_en": "Doxxing = publishing someone’s private identifying information without permission, often to intimidate or harm them.",
        "word_ar": "Doxxing = نشر معلومات تعريفية خاصة بشخص دون إذنه، غالبًا بهدف التخويف أو الإضرار به.",
        "video": "r66gK1IENcs",
        "caption_en": "eSafety guidance related to adult cyber abuse.",
        "caption_ar": "إرشادات من eSafety حول الإساءة والمضايقة عبر الإنترنت.",
        "resource": "https://www.esafety.gov.au/key-topics/adult-cyber-abuse",
        "resource_name": "eSafety",
        "quiz_q_en": "What is useful before blocking a harassing account?",
        "quiz_q_ar": "ما الذي من المفيد فعله قبل حظر حساب يضايقك؟",
        "quiz_options_en": ["Delete everything immediately", "Preserve relevant evidence such as screenshots", "Send them your location"],
        "quiz_options_ar": ["حذف كل شيء فورًا", "حفظ الأدلة المهمة مثل لقطات الشاشة", "إرسال موقعك للشخص"],
        "correct": 1,
    },
    "blackmail": {
        "label_en": "⚠️ Blackmail & Sextortion",
        "label_ar": "⚠️ الابتزاز والابتزاز الجنسي",
        "title_en": "Blackmail & Sextortion",
        "title_ar": "الابتزاز والابتزاز الجنسي",
        "what_en": "Blackmail uses threats to pressure someone into sending money, information, or doing something. Sextortion is a form of blackmail involving intimate or sexual content.",
        "what_ar": "الابتزاز يستخدم التهديد للضغط على شخص لإرسال مال أو معلومات أو القيام بشيء معين. والابتزاز الجنسي هو نوع من الابتزاز يرتبط بمحتوى حميمي أو جنسي.",
        "example_en": "Someone threatens to share a private image unless you send money or more images.",
        "example_ar": "شخص يهدد بنشر صورة خاصة ما لم ترسلي مالًا أو صورًا إضافية.",
        "danger_en": "Paying or sending more content does not guarantee the threats will stop and may give the blackmailer more leverage.",
        "danger_ar": "دفع المال أو إرسال المزيد من المحتوى لا يضمن توقف التهديد، وقد يعطي المبتز وسائل ضغط إضافية.",
        "signs_en": ["Threats to publish private material", "Demands for money or more content", "Pressure to keep the situation secret", "Rapid escalation after trust is gained"],
        "signs_ar": ["التهديد بنشر مواد خاصة", "طلب المال أو المزيد من المحتوى", "الضغط لإبقاء الموضوع سرًا", "تصاعد سريع بعد كسب الثقة"],
        "actions_en": ["Do not send more money, private content, passwords, or verification codes.", "Preserve evidence before blocking or deleting.", "Secure your accounts and privacy settings.", "Seek help from a trusted person and appropriate official or professional support."],
        "actions_ar": ["لا ترسلي المزيد من المال أو المحتوى الخاص أو كلمات المرور أو رموز التحقق.", "احفظي الأدلة قبل الحظر أو الحذف.", "أمّني حساباتك وإعدادات الخصوصية.", "اطلبي المساعدة من شخص موثوق وجهة رسمية أو مهنية مناسبة."],
        "word_en": "Sextortion = blackmail involving intimate images, videos, messages, or sexual content.",
        "word_ar": "Sextortion (الابتزاز الجنسي) = ابتزاز يتضمن صورًا أو فيديوهات أو رسائل أو محتوى حميميًا أو جنسيًا.",
        "video": "PMv39d1LJgI",
        "caption_en": "FBI/NCMEC awareness information related to sextortion.",
        "caption_ar": "معلومات توعوية من FBI/NCMEC حول الابتزاز الجنسي.",
        "resource": "https://www.fbi.gov/how-we-can-help-you/scams-and-safety/common-frauds-and-scams/sextortion",
        "resource_name": "FBI",
        "quiz_q_en": "If someone threatens to publish a private image unless you pay, which action is safer?",
        "quiz_q_ar": "إذا هدد شخص بنشر صورة خاصة ما لم تدفعي المال، أي تصرف أكثر أمانًا؟",
        "quiz_options_en": ["Keep paying until they promise to stop", "Preserve evidence, stop sending more, secure accounts, and seek trusted support", "Send your password so they can delete the image"],
        "quiz_options_ar": ["الاستمرار بالدفع حتى يعد بالتوقف", "حفظ الأدلة والتوقف عن الإرسال وتأمين الحسابات وطلب دعم موثوق", "إرسال كلمة المرور حتى يحذف الصورة"],
        "correct": 1,
    },
}


def render_learn():
    back_home()
    st.title(tr("📚 Learn", "📚 تعلّم"))

    st.write(
        tr(
            "Learn the basics of digital safety in simple language. No cybersecurity experience is needed.",
            "تعلّمي أساسيات السلامة الرقمية بلغة بسيطة. لا تحتاجين إلى أي خبرة سابقة في الأمن السيبراني.",
        )
    )

    st.markdown(
        tr(
            "<p style='color:#6F6675;font-size:16px;line-height:1.7;'>Each lesson includes a simple explanation, a real-life example, warning signs, safety steps, a video, and a quick quiz.</p>",
            "<p style='color:#6F6675;font-size:16px;line-height:1.8;'>يتضمن كل درس شرحًا بسيطًا، ومثالًا واقعيًا، وعلامات تحذيرية، وخطوات أمان، وفيديو، واختبارًا سريعًا.</p>",
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    lesson_keys = list(LESSONS.keys())
    selected_key = st.selectbox(
        tr("Choose a topic", "اختاري موضوعًا"),
        lesson_keys,
        index=None,
        placeholder=tr("Select a lesson", "اختاري درسًا"),
        format_func=lambda key: tr(LESSONS[key]["label_en"], LESSONS[key]["label_ar"]),
        key="learn_topic",
    )

    if selected_key is None:
        soft_card(
            tr(
                "👆 Choose a lesson above to start learning.",
                "👆 اختاري درسًا من الأعلى لبدء التعلّم.",
            ),
            "info",
            margin_top=16,
            margin_bottom=16,
        )
        return

    lesson = LESSONS[selected_key]
    st.markdown(f"# {tr(lesson['title_en'], lesson['title_ar'])}")

    st.markdown(tr("### 💡 What is it?", "### 💡 ما هو؟"))
    st.write(tr(lesson["what_en"], lesson["what_ar"]))

    st.markdown(tr("### 🧩 Simple Example", "### 🧩 مثال بسيط"))
    soft_card(tr(lesson["example_en"], lesson["example_ar"]), "info")

    st.markdown(tr("### ⚠️ Why is it dangerous?", "### ⚠️ لماذا هو خطير؟"))
    st.write(tr(lesson["danger_en"], lesson["danger_ar"]))

    st.markdown(tr("### 👀 Warning Signs", "### 👀 علامات تحذيرية"))
    signs = lesson["signs_ar"] if LANG == "AR" else lesson["signs_en"]
    for sign in signs:
        st.write(f"• {sign}")

    st.markdown(tr("### 🛡️ What should I do?", "### 🛡️ ماذا أفعل؟"))
    actions = lesson["actions_ar"] if LANG == "AR" else lesson["actions_en"]
    for action in actions:
        st.write(f"• {action}")

    st.markdown(tr("### 🧠 Cyber Words", "### 🧠 مصطلح سيبراني"))
    st.write(tr(lesson["word_en"], lesson["word_ar"]))

    watch_and_learn(
        lesson["video"],
        lesson["caption_en"],
        lesson["caption_ar"],
        lesson["resource"],
        lesson["resource_name"],
    )

    st.markdown(tr("### 🧠 Quick Quiz", "### 🧠 اختبار سريع"))
    options = lesson["quiz_options_ar"] if LANG == "AR" else lesson["quiz_options_en"]

    answer_index = st.radio(
        tr(lesson["quiz_q_en"], lesson["quiz_q_ar"]),
        options=list(range(len(options))),
        format_func=lambda idx: options[idx],
        index=None,
        key=f"quiz_{selected_key}",
    )

    if st.button(
        tr("✅ Check Answer", "✅ تحقق من الإجابة"),
        use_container_width=True,
        key=f"check_quiz_{selected_key}",
    ):
        if answer_index is None:
            st.warning(tr("Choose an answer first.", "اختاري إجابة أولًا."))
        elif answer_index == lesson["correct"]:
            st.success(tr("Correct! ✅", "إجابة صحيحة! ✅"))
        else:
            st.error(
                tr(
                    "Not quite. Review the lesson and try again.",
                    "ليست الإجابة الصحيحة. راجعي الدرس وحاولي مرة أخرى.",
                )
            )

# -----------------------------
# Page router
# -----------------------------
if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "check_message":
    render_check_message()
elif st.session_state.page == "privacy":
    render_privacy_checkup()
elif st.session_state.page == "help":
    render_help()
elif st.session_state.page == "learn":
    render_learn()
else:
    st.session_state.page = "home"
    st.rerun()
