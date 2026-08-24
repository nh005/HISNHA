import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Literal


# ==================================================
# PAGE SETTINGS
# ==================================================

st.set_page_config(
    page_title="HISNHA",
    page_icon="🛡️",
    layout="centered"
)


# ==================================================
# AI RESULT STRUCTURE
# ==================================================

class SafetyAnalysis(BaseModel):

    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Overall digital safety risk level."
    )

    threat_type: str = Field(
        description="The most likely type of digital threat."
    )

    reasons: list[str] = Field(
        description="2 to 4 short reasons explaining the risk."
    )

    actions: list[str] = Field(
        description="3 to 5 clear and practical safety actions."
    )


# ==================================================
# GEMINI CONNECTION
# ==================================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# ==================================================
# LEARN VIDEO HELPER
# ==================================================

def watch_and_learn(video_id, caption, resource_url, resource_name):

    st.markdown("### 🎥 Watch & Learn")

    st.image(
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        use_container_width=True
    )

    st.video(
        f"https://www.youtube.com/watch?v={video_id}"
    )

    st.caption(caption)

    st.link_button(
        f"🔗 Learn More — {resource_name}",
        resource_url,
        use_container_width=True
    )


# ==================================================
# NAVIGATION
# ==================================================

if "page" not in st.session_state:
    st.session_state.page = "home"


# ==================================================
# HOME
# ==================================================

if st.session_state.page == "home":

    st.image(
        "assets/hisnha_logo.png",
        width=280
    )

    st.write(
        "An AI-powered digital safety platform designed to help women "
        "and girls recognize online threats, strengthen their privacy, "
        "and respond safely to digital risks."
    )

    st.divider()

    st.subheader("How can we help you?")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🔍 Check a Message",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.page = "check_message"
            st.rerun()

        if st.button(
            "🔐 Privacy Checkup",
            use_container_width=True
        ):
            st.session_state.page = "privacy_checkup"
            st.rerun()

    with col2:

        if st.button(
            "🛡️ I Need Help",
            use_container_width=True
        ):
            st.session_state.page = "need_help"
            st.rerun()

        if st.button(
            "📚 Learn",
            use_container_width=True
        ):
            st.session_state.page = "learn"
            st.rerun()

    st.divider()

    st.caption(
        "🔒 Your privacy matters. Never enter passwords, OTP codes, "
        "private images, or highly sensitive personal information."
    )


# ==================================================
# CHECK A MESSAGE
# ==================================================

elif st.session_state.page == "check_message":

    if st.button("← Back"):
        st.session_state.page = "home"
        st.rerun()

    st.title("🔍 Check a Message")

    st.write(
        "Enter a message you'd like HISNHA to assess "
        "for possible digital safety risks."
    )

    message = st.text_area(
        "Message to analyze",
        placeholder="Enter the message here...",
        height=180
    )

    st.caption(
        "⚠️ Do not enter passwords, OTP codes, phone numbers, "
        "banking details, or other highly sensitive personal information."
    )

    if st.button(
        "Analyze Message",
        type="primary",
        use_container_width=True
    ):

        if message.strip() == "":

            st.warning("Please enter a message first.")

        else:

            try:

                with st.spinner(
                    "🛡️ HISNHA is analyzing the message..."
                ):

                    prompt = f"""
You are HISNHA, a digital safety assistant designed
primarily to help women and girls understand digital risks.

Your explanations must also be understandable to a person
with no cybersecurity knowledge.

Analyze the following message for possible cybersecurity
and digital-safety risks.


MESSAGE:

{message}


==================================================
RISK CLASSIFICATION RULES
==================================================

LOW RISK:

Choose LOW when:

- The message appears normal or harmless.
- There is no clear suspicious behavior.
- There is no request for sensitive information.
- There is no suspicious pressure, threat, or manipulation.
- The message is ordinary conversation.


MEDIUM RISK:

Choose MEDIUM when:

- The message contains suspicious urgency or pressure.
- There is a vague request to confirm account information.
- The sender is trying to make the user act quickly.
- The message mentions a possible account problem but does not
  directly request highly sensitive information.
- There are suspicious signs, but there is not enough evidence
  for a clear high-risk attack.

IMPORTANT:

A vague request for "account information" alone should NOT
automatically be HIGH.


HIGH RISK:

Choose HIGH when there is a strong or direct digital threat,
such as:

- Asking for a password.
- Asking for an OTP.
- Asking for a verification code.
- Asking for banking or payment credentials.
- Asking for highly sensitive personal information.
- A clear attempt to take over an account.
- Clear credential theft.
- Blackmail or extortion.
- Serious online threats.
- Requests for private or intimate content.
- A clear impersonation attempt combined with harmful requests.
- A suspicious link clearly designed to collect login details
  or other sensitive information.


==================================================
THREATS TO LOOK FOR
==================================================

Look for risks including:

- Phishing
- Social Engineering
- Credential Theft
- Account Takeover Attempts
- Impersonation
- Online Harassment
- Blackmail
- Scam Attempts
- Suspicious Links
- Requests for Passwords
- Requests for Verification Codes


==================================================
EXPLANATION RULES
==================================================

Your explanation must:

- Use simple and clear English.
- Be understandable to someone with no cybersecurity background.
- Explain the behavior that makes the message risky.
- Avoid unnecessary technical language.
- If you use a cybersecurity term, explain it simply.
- Give 2 to 4 short reasons.
- Give 3 to 5 practical safety actions.
- Focus only on relevant digital-safety risks.


==================================================
IMPORTANT ACCURACY RULES
==================================================

Do NOT make absolute claims about companies, websites,
social media platforms, banks, or organizations.

Do NOT write statements such as:

- "Legitimate organizations will never ask..."
- "Instagram will never ask..."
- "Banks always..."
- "Official platforms never..."
- "Companies will never..."

Avoid the words "never" and "always" when describing
how an organization or platform behaves.

Instead, explain the risky behavior itself.

For example, if the message asks the user to send a
verification code to another person, say something like:

"A request to send a verification code to another person
is a strong warning sign because that code may be used
to access an account."

You may advise the user to verify an account issue by
opening the official app or website directly.

Absolute safety instructions directed to the USER are allowed
when appropriate, for example:

"Never share your password or verification code with another person."


==================================================
SAFETY RULES
==================================================

- Follow the LOW, MEDIUM, and HIGH definitions above.
- Do not classify something as HIGH only because it sounds unusual.
- Do not exaggerate the danger.
- Do not accuse a person of being a criminal with certainty.
- Do not ask the user for passwords.
- Do not ask for OTP codes.
- Do not ask for banking details.
- Do not ask for private images.
- Do not ask for highly sensitive personal information.
- Do not claim with certainty that a sender is malicious
  unless the message itself clearly demonstrates the risky behavior.
"""

                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            response_mime_type="application/json",
                            response_schema=SafetyAnalysis
                        )
                    )

                    analysis = response.parsed

                    if analysis is None:
                        analysis = SafetyAnalysis.model_validate_json(
                            response.text
                        )

                st.divider()

                st.subheader("🛡️ HISNHA Safety Analysis")

                if analysis.risk_level == "HIGH":

                    st.error("🔴 HIGH RISK")

                elif analysis.risk_level == "MEDIUM":

                    st.warning("🟠 MEDIUM RISK")

                else:

                    st.success("🟢 LOW RISK")

                st.markdown("### ⚠️ Threat Type")

                st.info(
                    analysis.threat_type
                )

                st.markdown(
                    "### 🔍 Why is this suspicious?"
                )

                for reason in analysis.reasons:

                    st.markdown(
                        f"- {reason}"
                    )

                st.markdown(
                    "### 🛡️ What should you do?"
                )

                for number, action in enumerate(
                    analysis.actions,
                    start=1
                ):

                    st.markdown(
                        f"**{number}.** {action}"
                    )

                st.divider()

                st.info(
                    "💜 Remember: Never share passwords, OTP codes, "
                    "verification codes, or other highly sensitive "
                    "personal information."
                )

                st.caption(
                    "HISNHA provides digital-safety guidance. "
                    "The current prototype does not save the message "
                    "in its own database."
                )

            except Exception as error:

                st.error(
                    "Something went wrong while analyzing the message."
                )

                st.code(
                    str(error)
                )


# ==================================================
# PRIVACY CHECKUP
# ==================================================

elif st.session_state.page == "privacy_checkup":

    if st.button("← Back"):
        st.session_state.page = "home"
        st.rerun()

    st.title("🔐 Privacy Checkup")

    st.write(
        "Answer a few quick questions to check your current "
        "digital safety habits."
    )

    st.caption(
        "HISNHA does not ask for your passwords or private account details."
    )

    st.divider()

    q1 = st.radio(
        "1. Do you use Two-Factor Authentication (2FA) on your important accounts?",
        ["Select an answer", "Yes", "No"],
        key="q1"
    )

    q2 = st.radio(
        "2. Do you use a different password for each important account?",
        ["Select an answer", "Yes", "No"],
        key="q2"
    )

    q3 = st.radio(
        "3. Do you review which devices are logged into your accounts?",
        ["Select an answer", "Yes", "No"],
        key="q3"
    )

    q4 = st.radio(
        "4. Do you avoid opening suspicious links from unknown senders?",
        ["Select an answer", "Yes", "No"],
        key="q4"
    )

    q5 = st.radio(
        "5. Do you regularly review the privacy settings of your social media accounts?",
        ["Select an answer", "Yes", "No"],
        key="q5"
    )

    st.divider()

    if st.button(
        "Check My Safety Score",
        type="primary",
        use_container_width=True
    ):

        answers = [
            q1,
            q2,
            q3,
            q4,
            q5
        ]

        if "Select an answer" in answers:

            st.warning(
                "Please answer all questions before checking your score."
            )

        else:

            score = 0
            recommendations = []

            if q1 == "Yes":

                score += 20

            else:

                recommendations.append(
                    "Enable Two-Factor Authentication (2FA) "
                    "on important accounts."
                )

            if q2 == "Yes":

                score += 20

            else:

                recommendations.append(
                    "Use a unique password for each important account."
                )

            if q3 == "Yes":

                score += 20

            else:

                recommendations.append(
                    "Regularly review devices that are logged "
                    "into your accounts."
                )

            if q4 == "Yes":

                score += 20

            else:

                recommendations.append(
                    "Avoid opening unexpected or suspicious links "
                    "from unknown senders."
                )

            if q5 == "Yes":

                score += 20

            else:

                recommendations.append(
                    "Review your social media privacy settings regularly."
                )

            st.divider()

            st.subheader(
                "🛡️ Your Digital Safety Score"
            )

            st.progress(
                score / 100
            )

            st.metric(
                label="Safety Score",
                value=f"{score}/100"
            )

            if score >= 80:

                st.success(
                    "🟢 Strong Digital Safety"
                )

                st.write(
                    "You are following many good digital safety practices."
                )

            elif score >= 60:

                st.warning(
                    "🟠 Good, but there is room to improve"
                )

                st.write(
                    "Your digital safety habits are generally good, "
                    "but a few improvements can make your accounts safer."
                )

            else:

                st.error(
                    "🔴 Your Digital Safety Needs Attention"
                )

                st.write(
                    "Several important security practices can be improved."
                )

            if recommendations:

                st.markdown(
                    "### 💡 Recommendations"
                )

                for recommendation in recommendations:

                    st.markdown(
                        f"- {recommendation}"
                    )

            else:

                st.markdown(
                    "### 💜 Great job!"
                )

                st.write(
                    "You are already following all of the safety "
                    "practices included in this checkup."
                )

            st.caption(
                "This score is a simple awareness tool and is not "
                "a complete cybersecurity assessment."
            )


# ==================================================
# I NEED HELP
# ==================================================

elif st.session_state.page == "need_help":

    if st.button("← Back"):

        st.session_state.page = "home"
        st.rerun()

    st.title("🛡️ I Need Help")

    st.write(
        "Choose the situation that best describes what happened. "
        "HISNHA will give you simple steps you can follow."
    )

    st.caption(
        "🔒 You do not need to enter names, passwords, private messages, "
        "or other sensitive information."
    )

    st.divider()

    situation = st.selectbox(
        "What happened?",
        [
            "Select a situation",
            "My account may have been hacked",
            "Someone is impersonating me online",
            "Someone is threatening or blackmailing me",
            "I am being harassed online",
            "I received a suspicious link"
        ]
    )

    if situation != "Select a situation":

        st.divider()


        # ==================================================
        # HACKED ACCOUNT
        # ==================================================

        if situation == "My account may have been hacked":

            st.subheader(
                "🔐 Your Account May Have Been Hacked"
            )

            st.write(
                "This can mean someone may have accessed your account "
                "without your permission."
            )

            st.markdown(
                "### 🚩 Possible Signs"
            )

            st.markdown(
                """
- You see a login you do not recognize.
- Your password suddenly stops working.
- Messages or posts appear that you did not create.
- Your recovery email or phone number was changed.
- You receive unexpected login alerts.
"""
            )

            st.markdown(
                "### 🛡️ Recommended Steps"
            )

            st.markdown(
                """
1. **Change your password** using the official app or website.

2. **Sign out of devices or sessions you do not recognize.**

3. **Check your recovery email and phone number** to make sure they were not changed.

4. **Enable Two-Factor Authentication (2FA)** if it is available.

5. **Review recent account activity** for actions you did not make.
"""
            )

            st.markdown(
                "### ❓ What if I can't log in?"
            )

            st.info(
                "Use the platform's official account recovery process. "
                "Do not pay or give your password to someone who claims "
                "they can recover the account for you."
            )


        # ==================================================
        # IMPERSONATION
        # ==================================================

        elif situation == "Someone is impersonating me online":

            st.subheader(
                "👤 Someone Is Pretending to Be You Online"
            )

            st.write(
                "This happens when someone uses your name, photo, "
                "or identity to make others believe they are you."
            )

            st.markdown(
                "### 🛡️ Recommended Steps"
            )

            st.markdown(
                """
1. **Save evidence first.** Keep the username, profile link, and useful screenshots.

2. **Do not argue with or give information to the fake account.**

3. **Report the account** using the platform's official impersonation or reporting tools.

4. **Block the account when appropriate** after saving the information you may need.

5. **Warn trusted contacts** if the fake account is messaging people you know.

6. **Review your privacy settings** and reduce unnecessary public information.
"""
            )

            st.markdown(
                "### ❓ What if they already contacted my friends?"
            )

            st.info(
                "Tell your contacts that the account is not you. "
                "Ask them not to send money, passwords, codes, "
                "or personal information to that account."
            )


        # ==================================================
        # BLACKMAIL
        # ==================================================

        elif situation == "Someone is threatening or blackmailing me":

            st.subheader(
                "⚠️ Threats or Blackmail"
            )

            st.write(
                "Blackmail is when someone uses threats to pressure you "
                "into giving them money, information, private content, "
                "or something else they demand."
            )

            st.markdown(
                "### 🛡️ Recommended Steps"
            )

            st.markdown(
                """
1. **Do not send more private content, passwords, money, or account information.**

2. **Preserve evidence before deleting or blocking anything.** Save relevant messages, usernames, dates, and screenshots.

3. **Avoid arguing or giving the person more personal information.**

4. **Secure your accounts** if you shared a password or other account information.

5. **Report and block the account when it is appropriate and safe to do so.**

6. **Tell someone you trust** and seek appropriate official or professional support if the threat is serious or ongoing.
"""
            )

            st.warning(
                "Paying or sending more private content does not guarantee "
                "that the threats will stop."
            )

            st.markdown(
                "### ❓ What if I already sent something?"
            )

            st.info(
                "Do not keep sending more because of new demands. "
                "Preserve the evidence and secure any accounts involved. "
                "If you transferred money, contact the bank or payment "
                "provider as soon as possible."
            )

            st.error(
                "If you believe you are in immediate physical danger, "
                "prioritize your personal safety and seek appropriate local help."
            )


        # ==================================================
        # ONLINE HARASSMENT
        # ==================================================

        elif situation == "I am being harassed online":

            st.subheader(
                "💬 Online Harassment"
            )

            st.write(
                "Online harassment can include repeated unwanted messages, "
                "abusive comments, threats, or someone repeatedly trying "
                "to contact you after you want them to stop."
            )

            st.markdown(
                "### 🛡️ Recommended Steps"
            )

            st.markdown(
                """
1. **Avoid sharing additional personal information.**

2. **Save relevant evidence** if the behavior is repeated, threatening, or serious.

3. **Use block, mute, and report tools** available on the platform.

4. **Review who can message, tag, mention, or view your profile.**

5. **Reduce public personal information** such as unnecessary location details.

6. **Tell someone you trust** if the situation continues or is affecting your safety.
"""
            )

            st.markdown(
                "### ⚠️ When should I take it more seriously?"
            )

            st.warning(
                "If someone is threatening you, exposing private information, "
                "tracking you, or creating a real-world safety concern, "
                "do not treat it as only an annoying online message. "
                "Preserve evidence and seek appropriate trusted or official support."
            )


        # ==================================================
        # SUSPICIOUS LINK
        # ==================================================

        elif situation == "I received a suspicious link":

            st.subheader(
                "🔗 Suspicious Link"
            )

            st.write(
                "A suspicious link may lead to a fake website designed "
                "to steal login information, payment details, or other "
                "private information."
            )

            st.markdown(
                "### 🛡️ If You Have NOT Opened It"
            )

            st.markdown(
                """
1. **Do not open the link if you are unsure about it.**

2. **Do not enter passwords, OTP codes, or payment information through the link.**

3. **Open the official app or website yourself** instead of using the received link.

4. **Check who sent the message and why you received it.**

5. **Report or delete the suspicious message when appropriate.**
"""
            )

            st.markdown(
                "### ❓ What if I already clicked the link?"
            )

            st.info(
                "If you only opened the page and did not enter information, "
                "close it and avoid interacting with it."
            )

            st.markdown(
                "#### If you entered a password:"
            )

            st.markdown(
                """
- Go to the **real official website or app**.
- Change the affected password.
- Enable **2FA** if available.
- Review logged-in devices and recent account activity.
"""
            )

            st.markdown(
                "#### If you entered payment information:"
            )

            st.warning(
                "Contact your bank or payment provider as soon as possible "
                "using their official contact information."
            )

            st.markdown(
                "#### If the link downloaded a file:"
            )

            st.write(
                "Do not open an unexpected downloaded file. "
                "Use your device's trusted security or antivirus tools "
                "to check it."
            )


        # ==================================================
        # HELP FOOTER
        # ==================================================

        st.divider()

        st.info(
            "💜 HISNHA provides general digital-safety guidance. "
            "You do not need to share sensitive details to use this section."
        )


# ==================================================
# LEARN
# ==================================================

elif st.session_state.page == "learn":

    if st.button("← Back"):

        st.session_state.page = "home"
        st.rerun()

    st.title("📚 Learn")

    st.write(
        "Learn the basics of digital safety in simple language. "
        "No cybersecurity experience is needed."
    )

    st.caption(
        "Each lesson includes a simple explanation, a real-life example, "
        "warning signs, safety steps, a video, and a quick quiz."
    )

    st.divider()

    topic = st.selectbox(
        "Choose a topic",
        [
            "Select a lesson",
            "🎣 Phishing",
            "🔑 Strong Passwords",
            "🔐 Two-Factor Authentication",
            "👤 Fake Accounts & Impersonation",
            "💬 Online Harassment",
            "⚠️ Blackmail & Sextortion"
        ]
    )


    # ==================================================
    # PHISHING
    # ==================================================

    if topic == "🎣 Phishing":

        st.header(
            "🎣 Phishing"
        )

        st.markdown(
            "### 💡 What is Phishing?"
        )

        st.write(
            "Phishing is when someone sends you a fake or misleading "
            "message to make you reveal private information or take "
            "an unsafe action."
        )

        st.write(
            "They may try to get your password, verification code, "
            "banking information, or make you open a suspicious link."
        )

        st.markdown(
            "### 💬 Simple Example"
        )

        st.info(
            "\"Your account will be suspended today. "
            "Send me the verification code you just received.\""
        )

        st.markdown(
            "### ⚠️ Why Can It Be Dangerous?"
        )

        st.write(
            "If you give the sender your login information or verification "
            "code, they may be able to access your account, change your "
            "password, or misuse your personal information."
        )

        st.markdown(
            "### 🚩 Warning Signs"
        )

        st.markdown(
            """
- The message creates panic or urgency.
- Someone asks for your password or verification code.
- You receive an unexpected link.
- The sender asks for sensitive personal information.
- The message pressures you to act immediately.
"""
        )

        st.markdown(
            "### 🛡️ What Should You Do?"
        )

        st.markdown(
            """
1. Stop before clicking or replying.
2. Do not share passwords or verification codes.
3. Open the official app or website yourself.
4. Check who actually sent the message.
5. Block or report suspicious accounts when appropriate.
"""
        )

        st.markdown(
            "### 📖 Cyber Word"
        )

        st.info(
            "**Phishing:** A trick used to make someone reveal "
            "private information or perform an unsafe action."
        )

        watch_and_learn(
            "JlQovysQBn0",
            "Recognize and Report Phishing — CISA",
            "https://www.cisa.gov/secure-our-world/recognize-and-report-phishing",
            "CISA"
        )

        st.divider()

        st.markdown(
            "### 🧠 Quick Quiz"
        )

        phishing_answer = st.radio(
            "Which message is the most suspicious?",
            [
                "Choose an answer",
                "Are we still meeting tomorrow?",
                "Your account is at risk. Send me your verification code now.",
                "Happy birthday! Hope you have a great day."
            ],
            key="phishing_quiz"
        )

        if st.button(
            "Check Answer",
            key="check_phishing_answer"
        ):

            if phishing_answer == "Choose an answer":

                st.warning(
                    "Please choose an answer."
                )

            elif phishing_answer == (
                "Your account is at risk. "
                "Send me your verification code now."
            ):

                st.success(
                    "✅ Correct! The message creates urgency and asks "
                    "for a sensitive verification code."
                )

            else:

                st.error(
                    "❌ Not quite. Look for urgency and requests "
                    "for sensitive information."
                )


    # ==================================================
    # STRONG PASSWORDS
    # ==================================================

    elif topic == "🔑 Strong Passwords":

        st.header(
            "🔑 Strong Passwords"
        )

        st.markdown(
            "### 💡 What is a Password?"
        )

        st.write(
            "A password is like a digital key. It helps prove that "
            "you are the person allowed to access an account."
        )

        st.write(
            "A strong password should be difficult for another person "
            "to guess and should not be reused across important accounts."
        )

        st.markdown(
            "### 💬 Simple Example"
        )

        st.write(
            "A weak password might be:"
        )

        st.code(
            "mera123"
        )

        st.write(
            "A safer approach is using a long and unique password "
            "or passphrase that is not based on obvious personal information."
        )

        st.markdown(
            "### ⚠️ Why Can Weak Passwords Be Dangerous?"
        )

        st.write(
            "If the same password is used on several accounts and one "
            "account is compromised, the same password may be tried "
            "on your other accounts."
        )

        st.markdown(
            "### 🚩 Risky Password Habits"
        )

        st.markdown(
            """
- Using the same password everywhere
- Using your name or birthday
- Using very short passwords
- Sharing passwords with other people
- Keeping important passwords in unsafe places
"""
        )

        st.markdown(
            "### 🛡️ Better Password Habits"
        )

        st.markdown(
            """
1. Use a different password for important accounts.
2. Make passwords long and difficult to guess.
3. Avoid obvious personal information.
4. Consider using a trusted password manager.
5. Change a password if you believe it has been exposed.
"""
        )

        st.markdown(
            "### 📖 Cyber Words"
        )

        st.info(
            "**Unique Password:** A password used for only one account.\n\n"
            "**Passphrase:** A longer password made from several words "
            "or a memorable phrase."
        )

        watch_and_learn(
            "FZoB7yUGh7Y",
            "Stop Online Crime with Strong Passwords — CISA",
            "https://www.cisa.gov/secure-our-world/use-strong-passwords",
            "CISA"
        )

        st.divider()

        st.markdown(
            "### 🧠 Quick Quiz"
        )

        password_answer = st.radio(
            "Which is the safer habit?",
            [
                "Choose an answer",
                "Using the same password everywhere",
                "Using different passwords for important accounts",
                "Sharing your password with a close friend"
            ],
            key="password_quiz"
        )

        if st.button(
            "Check Answer",
            key="check_password_answer"
        ):

            if password_answer == "Choose an answer":

                st.warning(
                    "Please choose an answer."
                )

            elif password_answer == (
                "Using different passwords for important accounts"
            ):

                st.success(
                    "✅ Correct! Unique passwords reduce the damage "
                    "if one account is compromised."
                )

            else:

                st.error(
                    "❌ Try again. Reusing or sharing passwords "
                    "can increase your risk."
                )


    # ==================================================
    # TWO-FACTOR AUTHENTICATION
    # ==================================================

    elif topic == "🔐 Two-Factor Authentication":

        st.header(
            "🔐 Two-Factor Authentication"
        )

        st.markdown(
            "### 💡 What is 2FA?"
        )

        st.write(
            "Two-Factor Authentication, usually called 2FA, is like "
            "adding a second lock to your account."
        )

        st.write(
            "Instead of using only your password, the account asks for "
            "another verification step before allowing access."
        )

        st.markdown(
            "### 💬 Simple Example"
        )

        st.code(
            "Password\n"
            "   +\n"
            "Second verification step\n"
            "   =\n"
            "Account Access"
        )

        st.write(
            "The second step may use an authenticator app, security key, "
            "or another verification method."
        )

        st.markdown(
            "### ⚠️ Why is 2FA Important?"
        )

        st.write(
            "If someone learns your password, the second verification "
            "step can make it harder for them to access your account."
        )

        st.markdown(
            "### 🚩 Important Warning"
        )

        st.warning(
            "A verification code is sensitive. Do not send a code "
            "to another person just because they ask for it."
        )

        st.markdown(
            "### 🛡️ What Should You Do?"
        )

        st.markdown(
            """
1. Turn on 2FA for important accounts when available.
2. Protect your verification methods.
3. Never send authentication codes to another person.
4. Review unexpected login notifications.
5. Keep recovery options updated and secure.
"""
        )

        st.markdown(
            "### 📖 Cyber Words"
        )

        st.info(
            "**2FA:** Two-Factor Authentication.\n\n"
            "**OTP:** One-Time Password — a temporary code used "
            "during a verification process."
        )

        watch_and_learn(
            "XIlF2qkav5c",
            "Make Your Accounts Safer with Multifactor Authentication — CISA",
            "https://www.cisa.gov/secure-our-world/turn-mfa",
            "CISA"
        )

        st.divider()

        st.markdown(
            "### 🧠 Quick Quiz"
        )

        twofa_answer = st.radio(
            "What is the main purpose of 2FA?",
            [
                "Choose an answer",
                "To make your username longer",
                "To add another layer of account security",
                "To make your profile private automatically"
            ],
            key="twofa_quiz"
        )

        if st.button(
            "Check Answer",
            key="check_twofa_answer"
        ):

            if twofa_answer == "Choose an answer":

                st.warning(
                    "Please choose an answer."
                )

            elif twofa_answer == (
                "To add another layer of account security"
            ):

                st.success(
                    "✅ Correct! 2FA adds another verification step "
                    "in addition to your password."
                )

            else:

                st.error(
                    "❌ Try again."
                )


    # ==================================================
    # IMPERSONATION
    # ==================================================

    elif topic == "👤 Fake Accounts & Impersonation":

        st.header(
            "👤 Fake Accounts & Impersonation"
        )

        st.markdown(
            "### 💡 What is Online Impersonation?"
        )

        st.write(
            "Online impersonation is when someone creates or uses an "
            "account to pretend to be another person."
        )

        st.write(
            "They may copy someone's name, profile photo, information, "
            "or communication style."
        )

        st.markdown(
            "### 💬 Simple Example"
        )

        st.info(
            "Someone creates a new account using your name and photo, "
            "then starts messaging your friends while pretending to be you."
        )

        st.markdown(
            "### ⚠️ Why Can It Be Dangerous?"
        )

        st.write(
            "A fake account may be used to damage someone's reputation, "
            "mislead friends, request money, collect information, or "
            "contact other people while pretending to be the real person."
        )

        st.markdown(
            "### 🚩 Warning Signs"
        )

        st.markdown(
            """
- A second account suddenly appears using the same name or photos.
- The username is slightly different from the real account.
- The account sends unusual requests for money or information.
- The writing style or behavior seems different.
- Friends receive unexpected messages supposedly from you.
"""
        )

        st.markdown(
            "### 🛡️ What Should You Do?"
        )

        st.markdown(
            """
1. Verify the identity through another trusted method.
2. Do not send sensitive information to the suspicious account.
3. Save relevant evidence such as the username or profile link.
4. Report impersonation using the platform's reporting tools.
5. Warn trusted contacts if someone is pretending to be you.
"""
        )

        st.markdown(
            "### 📖 Cyber Word"
        )

        st.info(
            "**Impersonation:** Pretending to be another person online."
        )

        watch_and_learn(
            "-89h8FGgypQ",
            "Let's Talk About How Impersonation Scams Work — FTC",
            "https://consumer.ftc.gov/features/how-avoid-imposter-scams",
            "FTC Consumer Advice"
        )

        st.divider()

        st.markdown(
            "### 🧠 Quick Quiz"
        )

        impersonation_answer = st.radio(
            "What is a possible sign of impersonation?",
            [
                "Choose an answer",
                "A friend changes their profile color",
                "A new account uses your name and photo and contacts your friends",
                "Someone likes your public post"
            ],
            key="impersonation_quiz"
        )

        if st.button(
            "Check Answer",
            key="check_impersonation_answer"
        ):

            if impersonation_answer == "Choose an answer":

                st.warning(
                    "Please choose an answer."
                )

            elif impersonation_answer == (
                "A new account uses your name and photo and contacts your friends"
            ):

                st.success(
                    "✅ Correct! Copying someone's identity and contacting "
                    "others as that person can be a sign of impersonation."
                )

            else:

                st.error(
                    "❌ Try again."
                )


    # ==================================================
    # ONLINE HARASSMENT
    # ==================================================

    elif topic == "💬 Online Harassment":

        st.header(
            "💬 Online Harassment"
        )

        st.markdown(
            "### 💡 What is Online Harassment?"
        )

        st.write(
            "Online harassment is unwanted or abusive behavior directed "
            "at someone through digital platforms."
        )

        st.write(
            "It can include repeated unwanted messages, insulting comments, "
            "threats, stalking behavior, or repeated attempts to contact someone."
        )

        st.markdown(
            "### 💬 Simple Example"
        )

        st.info(
            "You block an account after receiving abusive messages, "
            "but the person creates new accounts and continues contacting you."
        )

        st.markdown(
            "### ⚠️ Why Can It Be Harmful?"
        )

        st.write(
            "Online harassment can affect privacy, emotional wellbeing, "
            "reputation, and in serious situations may also create "
            "real-world safety concerns."
        )

        st.markdown(
            "### 🚩 Warning Signs"
        )

        st.markdown(
            """
- Repeated unwanted messages
- Threatening or abusive comments
- Someone repeatedly creating new accounts to contact you
- Attempts to publicly expose your personal information
- Persistent unwanted tagging, mentioning, or messaging
"""
        )

        st.markdown(
            "### 🛡️ What Should You Do?"
        )

        st.markdown(
            """
1. Avoid sharing additional personal information.
2. Save relevant evidence if the behavior is serious or repeated.
3. Use block, mute, and report tools.
4. Review who can message, tag, or view your profile.
5. Tell someone you trust if the situation continues or affects your safety.
"""
        )

        st.markdown(
            "### 📖 Cyber Word"
        )

        st.info(
            "**Online Harassment:** Repeated or harmful unwanted behavior "
            "directed at someone through digital platforms."
        )

        watch_and_learn(
            "r66gK1IENcs",
            "How eSafety Can Help You Deal with Adult Cyber Abuse — eSafety",
            "https://www.esafety.gov.au/key-topics/adult-cyber-abuse",
            "eSafety"
        )

        st.divider()

        st.markdown(
            "### 🧠 Quick Quiz"
        )

        harassment_answer = st.radio(
            "Which situation is the clearest example of online harassment?",
            [
                "Choose an answer",
                "Someone disagrees with one of your posts",
                "Someone repeatedly sends abusive messages after you ask them to stop",
                "A friend sends you a funny video"
            ],
            key="harassment_quiz"
        )

        if st.button(
            "Check Answer",
            key="check_harassment_answer"
        ):

            if harassment_answer == "Choose an answer":

                st.warning(
                    "Please choose an answer."
                )

            elif harassment_answer == (
                "Someone repeatedly sends abusive messages after you ask them to stop"
            ):

                st.success(
                    "✅ Correct! Repeated unwanted abusive behavior "
                    "is a strong sign of online harassment."
                )

            else:

                st.error(
                    "❌ Try again."
                )


    # ==================================================
    # BLACKMAIL & SEXTORTION
    # ==================================================

    elif topic == "⚠️ Blackmail & Sextortion":

        st.header(
            "⚠️ Blackmail & Sextortion"
        )

        st.markdown(
            "### 💡 What is Digital Blackmail?"
        )

        st.write(
            "Digital blackmail is when someone threatens to reveal, "
            "share, or misuse private information or content unless "
            "you do what they demand."
        )

        st.markdown(
            "### 💡 What is Sextortion?"
        )

        st.write(
            "Sextortion is a form of blackmail involving private or "
            "intimate images, videos, or conversations."
        )

        st.markdown(
            "### 💬 Simple Example"
        )

        st.info(
            "Someone says: \"Send me money or I will share your "
            "private photos with your friends.\""
        )

        st.markdown(
            "### ⚠️ Why Can It Be Dangerous?"
        )

        st.write(
            "The person may keep making new demands, threaten your privacy, "
            "or use fear to pressure you into sending money, information, "
            "or more private content."
        )

        st.markdown(
            "### 🚩 Warning Signs"
        )

        st.markdown(
            """
- Threats to expose private content
- Demands for money
- Demands for more photos or personal information
- Pressure to act immediately
- Threats to contact family, friends, school, or workplace
"""
        )

        st.markdown(
            "### 🛡️ What Should You Do?"
        )

        st.markdown(
            """
1. Do not send additional private content or account credentials.
2. Preserve relevant evidence such as messages, usernames, and dates.
3. Avoid giving the person more personal information.
4. Use reporting and blocking tools when appropriate and safe.
5. Tell someone you trust and seek appropriate official or professional support if the threat is serious or ongoing.
"""
        )

        st.warning(
            "If you believe the situation may create immediate physical "
            "danger, prioritize your personal safety and seek appropriate local help."
        )

        st.markdown(
            "### 📖 Cyber Words"
        )

        st.info(
            "**Blackmail:** Threatening someone in order to force them "
            "to do something.\n\n"
            "**Sextortion:** Blackmail involving private or intimate content."
        )

        watch_and_learn(
            "PMv39d1LJgI",
            "FBI and NCMEC: Sextortion Awareness",
            "https://www.fbi.gov/how-we-can-help-you/scams-and-safety/common-frauds-and-scams/sextortion",
            "FBI"
        )

        st.divider()

        st.markdown(
            "### 🧠 Quick Quiz"
        )

        blackmail_answer = st.radio(
            "What is the safest response to a blackmail threat?",
            [
                "Choose an answer",
                "Send more private information so the person stops",
                "Keep relevant evidence and avoid sending more sensitive content",
                "Give the person your password"
            ],
            key="blackmail_quiz"
        )

        if st.button(
            "Check Answer",
            key="check_blackmail_answer"
        ):

            if blackmail_answer == "Choose an answer":

                st.warning(
                    "Please choose an answer."
                )

            elif blackmail_answer == (
                "Keep relevant evidence and avoid sending more sensitive content"
            ):

                st.success(
                    "✅ Correct! Avoid giving the person more sensitive "
                    "material and preserve relevant evidence."
                )

            else:

                st.error(
                    "❌ Try again. Sending more sensitive information "
                    "can increase the risk."
                )


    # ==================================================
    # NOTHING SELECTED
    # ==================================================

    else:

        st.info(
            "👆 Choose a lesson above to start learning."
        )