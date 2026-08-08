from verifying_passcode import verify_user, add_user, reset_password, get_db_connection
from nicegui import ui, app
import school_home_page
import teacher_page
import lower
from insert import insert
from datetime import datetime


# ============================================================
# ADMIN ACCOUNTS
# ============================================================

ADMIN_ACCOUNTS = {
    "Apostle": "password1234",
    "Principal": "AdminPass2026",
    "Headmaster": "Secret123",
    "admin_account": "password1234",
}

ADMIN_LOOKUP = {
    username.strip().lower(): password
    for username, password in ADMIN_ACCOUNTS.items()
}


def is_admin_username(username: str) -> bool:
    if not username:
        return False
    return username.strip().lower() in ADMIN_LOOKUP


def authenticate_user(username: str, password: str) -> bool:
    if not username or not password:
        return False

    username_key = username.strip().lower()

    if username_key in ADMIN_LOOKUP and ADMIN_LOOKUP[username_key] == password:
        return True

    try:
        return bool(verify_user(username.strip(), password))
    except Exception as e:
        print(f"verify_user error: {e}")
        return False


# ============================================================
# LOGIN ACTIVITY LOG
# ============================================================
def update_login_activity(username, status='Active'):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT, 
                timestamp TEXT,
                status TEXT
            )
        ''')

        if status == 'Active':
            cursor.execute("""
                UPDATE activity_logs
                SET status = 'Inactive'
                WHERE status = 'Active'
            """)

        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        cursor.execute('''
            INSERT INTO activity_logs (username, timestamp, status) 
            VALUES (?, ?, ?)
        ''', (username, current_timestamp, status))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Activity log error: {e}")


# ============================================================
# GLOBAL UI SETTINGS (STRICT 3-COLOR PALETTE)
# ============================================================
# 1. Primary: Dark Emerald Green (#064e3b)
# 2. Secondary: Pure White (#ffffff)
# 3. Accent: Vibrant Emerald (#10b981)
ui.colors(primary='#064e3b', secondary='#ffffff', accent='#10b981')


# ============================================================
# CUSTOM UI ANIMATIONS & THEME OVERRIDES
# ============================================================
ui.add_css('''
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up {
    animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(3deg); }
}
.animate-float {
    animation: float 8s ease-in-out infinite;
}

/* Input Styling */
.q-field--outlined .q-field__control {
    border-radius: 14px !important;
    min-height: 54px !important;
    background-color: #f9fafb !important;
}
.q-field--outlined .q-field__control:before {
    border-color: #e5e7eb !important;
    border-width: 1.5px !important;
}
.q-field--outlined.q-field--focused .q-field__control:after {
    border-color: #10b981 !important;
    border-width: 2px !important;
}
.q-field--outlined.q-field--focused .q-field__control {
    background-color: #ffffff !important;
}
.q-field__label {
    color: #6b7280 !important;
    font-size: 14px !important;
}
.q-field--focused .q-field__label {
    color: #064e3b !important;
}
.q-field__native, .q-field__input {
    color: #064e3b !important;
    font-size: 16px !important; /* Prevents iOS zoom on focus */
}
.q-field__marginal {
    color: #9ca3af !important;
}
.q-field--focused .q-field__marginal {
    color: #10b981 !important;
}

/* Tabs Styling */
.q-tabs__content {
    border-radius: 16px !important;
    overflow: hidden;
}
.q-tab {
    text-transform: none !important;
    letter-spacing: 0.05em !important;
    font-weight: 700 !important;
    color: #6b7280 !important;
    min-height: 44px !important;
    border-radius: 12px !important;
}
.q-tab--active {
    background-color: #064e3b !important;
    color: #ffffff !important;
    box-shadow: 0 4px 6px -1px rgba(6, 78, 59, 0.2) !important;
}
.q-tab__indicator {
    display: none !important;
}

/* Tab Panels */
.q-tab-panels {
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    background-color: transparent !important;
}
.q-tab-panel {
    background: transparent !important;
    padding: 0 !important;
}
''')


# SIMPLE REDIRECT HELPERS
def redirect_to_login():
    ui.label('Redirecting to login...').classes('text-lg font-semibold')
    ui.timer(0.1, lambda: ui.navigate.to('/login'), once=True)

def redirect_to_teacher():
    ui.label('Redirecting to teacher page...').classes('text-lg font-semibold')
    ui.timer(0.1, lambda: ui.navigate.to('/teacher'), once=True)


# PROTECTED PAGE WRAPPERS
def protected_home():
    if not app.storage.user.get('logged_in'):
        redirect_to_login()
        return
    current_user = app.storage.user.get('current_user', '')
    is_admin = app.storage.user.get('is_admin', False) or is_admin_username(current_user)
    if not is_admin:
        ui.notify('Home is for administrators only', type='negative', position='top')
        redirect_to_teacher()
        return
    school_home_page.home()

def protected_teacher():
    if not app.storage.user.get('logged_in'):
        redirect_to_login()
        return
    teacher_page.teacher()

def protected_insert():
    if not app.storage.user.get('logged_in'):
        redirect_to_login()
        return
    insert()

def lower_page():
    target = getattr(lower, 'lower', None)
    if callable(target):
        target()
    elif callable(lower):
        lower()
    else:
        ui.label('Lower page is not configured correctly.').classes('text-lg font-semibold')


# REDESIGNED LOGIN PAGE
def login_page():
    # Full-screen split layout
    with ui.element('div').classes('fixed inset-0 w-screen h-screen m-0 p-0 bg-[#f8faf9] overflow-y-auto flex flex-col lg:flex-row'):
        
        # ============================================================
        # LEFT PANEL (Branding - Hidden on Mobile)
        # ============================================================
        with ui.column().classes(
            'hidden lg:flex w-full lg:w-1/2 bg-[#064e3b] relative overflow-hidden items-center justify-center p-12'
        ):
            # Abstract decorative shapes (Strictly using White and Accent Green)
            ui.element('div').classes(
                'absolute -top-20 -left-20 w-96 h-96 rounded-full bg-[#10b981]/20 blur-3xl animate-float'
            )
            ui.element('div').classes(
                'absolute bottom-10 right-10 w-80 h-80 rounded-full bg-white/5 blur-2xl animate-float'
            ).style('animation-delay: 2s;')
            ui.element('div').classes(
                'absolute top-1/3 right-1/4 w-40 h-40 rounded-3xl border-4 border-[#10b981]/30 rotate-12'
            )
            ui.element('div').classes(
                'absolute bottom-1/4 left-1/4 w-32 h-32 rounded-full border-4 border-white/10'
            )

            with ui.column().classes('z-10 max-w-md gap-8 animate-fade-in-up'):
                with ui.row().classes('items-center gap-4'):
                    with ui.element('div').classes(
                        'w-16 h-16 rounded-2xl bg-white flex items-center justify-center shadow-xl'
                    ):
                        ui.icon('school').classes('text-4xl text-[#064e3b]')
                    
                ui.label('Institutional Portal').classes('text-4xl font-black tracking-tight text-white leading-tight')
                ui.label('Secure Access Management').classes('text-sm font-bold uppercase tracking-[0.25em] text-[#10b981]')
                
                ui.label(
                    'Access your administrative dashboard, teacher workspace, and school '
                    'management tools from one secure, unified entry point.'
                ).classes('text-lg leading-relaxed text-white/80')

                with ui.column().classes('gap-5 mt-4'):
                    with ui.row().classes('items-center gap-4'):
                        with ui.element('div').classes('w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center border border-white/10'):
                            ui.icon('person').classes('text-[#10b981] text-2xl')
                        ui.label('Role-based access control').classes('text-white font-medium text-lg')
                    
                    with ui.row().classes('items-center gap-4'):
                        with ui.element('div').classes('w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center border border-white/10'):
                            ui.icon('timeline').classes('text-[#10b981] text-2xl')
                        ui.label('Real-time activity monitoring').classes('text-white font-medium text-lg')
                        
                    with ui.row().classes('items-center gap-4'):
                        with ui.element('div').classes('w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center border border-white/10'):
                            ui.icon('lock').classes('text-[#10b981] text-2xl')
                        ui.label('Encrypted secure sessions').classes('text-white font-medium text-lg')

        # ============================================================
        # RIGHT PANEL (Login Form)
        # ============================================================
        with ui.column().classes(
            'w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12 overflow-y-auto'
        ):
            with ui.column().classes('w-full max-w-[480px] gap-6 animate-fade-in-up'):
                
                # Mobile Header (Visible only on mobile)
                with ui.column().classes('w-full items-center gap-3 mb-2 lg:hidden'):
                    with ui.element('div').classes(
                        'w-16 h-16 rounded-2xl bg-[#064e3b] flex items-center justify-center shadow-lg shadow-[#064e3b]/20'
                    ):
                        ui.icon('school').classes('text-3xl text-white')
                    ui.label('Institutional Portal').classes('text-2xl font-black tracking-tight text-[#064e3b] text-center')
                    ui.label('Secure Access Management').classes('text-xs font-bold uppercase tracking-[0.2em] text-gray-500 text-center')

                # Desktop Header
                with ui.column().classes('w-full mb-2 hidden lg:flex'):
                    ui.label('Welcome back').classes('text-3xl font-black tracking-tight text-[#064e3b]')
                    ui.label('Sign in to continue to your dashboard.').classes('text-base text-gray-500 mt-1')

                # Card Container
                with ui.card().classes(
                    'w-full rounded-3xl border border-gray-100 bg-white shadow-xl shadow-[#064e3b]/5 p-6 md:p-8'
                ).tight():
                    
                    # Tabs
                    with ui.tabs().classes(
                        'w-full rounded-2xl bg-gray-50 p-1.5 shadow-inner mb-6'
                    ) as tabs:
                        login_tab = ui.tab('login', label='Login').classes('flex-1')
                        register_tab = ui.tab('register', label='Register').classes('flex-1')
                        reset_tab = ui.tab('reset', label='Reset').classes('flex-1')

                    with ui.tab_panels(tabs, value=login_tab).classes('w-full bg-transparent p-0'):
                        
                        # ================= LOGIN TAB =================
                        with ui.tab_panel(login_tab).classes('p-0'):
                            with ui.column().classes('w-full gap-5'):
                                username_input = ui.input(label='Username').classes('w-full').props(
                                    'outlined dense hide-bottom-space placeholder="Enter your username"'
                                )
                                with username_input.add_slot('prepend'):
                                    ui.icon('person').classes('text-xl ml-3')

                                password_input = ui.input(
                                    label='Password', password=True, password_toggle_button=True
                                ).classes('w-full').props(
                                    'outlined dense hide-bottom-space placeholder="Enter your password"'
                                )
                                with password_input.add_slot('prepend'):
                                    ui.icon('lock').classes('text-xl ml-3')

                                with ui.row().classes('w-full justify-end -mt-2'):
                                    ui.link('Forgot password?', '#').on(
                                        'click', lambda: tabs.set_value(reset_tab)
                                    ).classes(
                                        'text-xs font-bold text-[#064e3b] hover:text-[#10b981] transition-colors cursor-pointer'
                                    )

                                with ui.button().classes(
                                    'w-full py-3.5 mt-2 rounded-2xl text-white font-bold text-sm tracking-wide '
                                    'bg-[#064e3b] hover:bg-[#065f46] active:scale-[0.98] transition-all '
                                    'shadow-lg shadow-[#064e3b]/20 justify-center items-center gap-2'
                                ).props('unelevated no-caps') as login_btn:
                                    login_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                                    ui.label('Sign In').classes('font-bold')

                                with ui.row().classes('w-full justify-center items-center gap-2 mt-4'):
                                    ui.label('New here?').classes('text-xs font-semibold text-gray-400')
                                    ui.link('Create an account', '#').on(
                                        'click', lambda: tabs.set_value(register_tab)
                                    ).classes(
                                        'text-xs font-bold text-[#10b981] hover:text-[#059669] transition-colors cursor-pointer'
                                    )

                            async def handle_page():
                                username = username_input.value.strip()
                                password = password_input.value
                                if not username or not password:
                                    ui.notify('Please fill the fields', type='warning', position='top')
                                    return
                                login_btn.disable()
                                login_spinner.classes(remove='hidden')
                                try:
                                    authenticated = authenticate_user(username, password)
                                    if authenticated:
                                        admin_user = is_admin_username(username)
                                        app.storage.user['logged_in'] = True
                                        app.storage.user['current_user'] = username
                                        app.storage.user['username'] = username
                                        app.storage.user['name'] = username
                                        app.storage.user['is_admin'] = admin_user
                                        update_login_activity(username, 'Active')
                                        ui.notify('Login successful!', type='positive', position='top')
                                        if admin_user:
                                            ui.navigate.to('/home')
                                        else:
                                            ui.navigate.to('/teacher')
                                    else:
                                        ui.notify('Invalid username or password', type='negative', position='top')
                                        login_btn.enable()
                                        login_spinner.classes(add='hidden')
                                except Exception as e:
                                    print(f"Login error: {e}")
                                    ui.notify(f'An error occurred: {e}', type='negative', position='top')
                                    login_btn.enable()
                                    login_spinner.classes(add='hidden')

                            login_btn.on_click(handle_page)
                            password_input.on('keydown.enter', handle_page)

                        # ================= REGISTER TAB =================
                        with ui.tab_panel(register_tab).classes('p-0'):
                            with ui.column().classes('w-full gap-5'):
                                reg_user = ui.input(label='Username').classes('w-full').props('outlined dense hide-bottom-space placeholder="Choose a username"')
                                with reg_user.add_slot('prepend'):
                                    ui.icon('person').classes('text-xl ml-3')

                                reg_email = ui.input(label='Email Address').classes('w-full').props('outlined dense hide-bottom-space type="email" placeholder="name@school.edu"')
                                with reg_email.add_slot('prepend'):
                                    ui.icon('email').classes('text-xl ml-3')

                                reg_pass = ui.input(label='Password', password=True, password_toggle_button=True).classes('w-full').props('outlined dense hide-bottom-space placeholder="Create a password"')
                                with reg_pass.add_slot('prepend'):
                                    ui.icon('lock').classes('text-xl ml-3')

                                with ui.button().classes(
                                    'w-full py-3.5 mt-2 rounded-2xl text-white font-bold text-sm tracking-wide '
                                    'bg-[#064e3b] hover:bg-[#065f46] active:scale-[0.98] transition-all '
                                    'shadow-lg shadow-[#064e3b]/20 justify-center items-center gap-2'
                                ).props('unelevated no-caps') as reg_btn:
                                    reg_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                                    ui.label('Create Account').classes('font-bold')

                                with ui.row().classes('w-full justify-center items-center gap-2 mt-4'):
                                    ui.label('Already have an account?').classes('text-xs font-semibold text-gray-400')
                                    ui.link('Sign in', '#').on('click', lambda: tabs.set_value(login_tab)).classes('text-xs font-bold text-[#10b981] hover:text-[#059669] transition-colors cursor-pointer')

                            async def handle_registration():
                                if not reg_user.value or not reg_email.value or not reg_pass.value:
                                    ui.notify('All fields are required!', type='warning', position='top')
                                    return
                                reg_btn.disable()
                                reg_spinner.classes(remove='hidden')
                                try:
                                    add_user(reg_user.value.strip(), reg_pass.value, reg_email.value.strip())
                                    ui.notify('Registration Successful!', type='positive', position='top')
                                    tabs.set_value(login_tab)
                                except Exception as e:
                                    print(f"Registration error: {e}")
                                    ui.notify('Registration failed.', type='negative', position='top')
                                finally:
                                    reg_btn.enable()
                                    reg_spinner.classes(add='hidden')

                            reg_btn.on_click(handle_registration)
                            reg_pass.on('keydown.enter', handle_registration)

                        # ================= RESET TAB =================
                        with ui.tab_panel(reset_tab).classes('p-0'):
                            with ui.column().classes('w-full gap-5'):
                                reset_user = ui.input(label='Username').classes('w-full').props('outlined dense hide-bottom-space placeholder="Enter your username"')
                                with reset_user.add_slot('prepend'):
                                    ui.icon('person').classes('text-xl ml-3')

                                reset_email = ui.input(label='Email Address').classes('w-full').props('outlined dense hide-bottom-space type="email" placeholder="name@school.edu"')
                                with reset_email.add_slot('prepend'):
                                    ui.icon('email').classes('text-xl ml-3')

                                reset_pass = ui.input(label='New Password', password=True, password_toggle_button=True).classes('w-full').props('outlined dense hide-bottom-space placeholder="Enter new password"')
                                with reset_pass.add_slot('prepend'):
                                    ui.icon('key').classes('text-xl ml-3')

                                with ui.button().classes(
                                    'w-full py-3.5 mt-2 rounded-2xl text-white font-bold text-sm tracking-wide '
                                    'bg-[#064e3b] hover:bg-[#065f46] active:scale-[0.98] transition-all '
                                    'shadow-lg shadow-[#064e3b]/20 justify-center items-center gap-2'
                                ).props('unelevated no-caps') as reset_btn:
                                    reset_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                                    ui.label('Reset Password').classes('font-bold')

                                with ui.row().classes('w-full justify-center items-center gap-2 mt-4'):
                                    ui.label('Remembered your password?').classes('text-xs font-semibold text-gray-400')
                                    ui.link('Back to Login', '#').on('click', lambda: tabs.set_value(login_tab)).classes('text-xs font-bold text-[#10b981] hover:text-[#059669] transition-colors cursor-pointer')

                            async def handle_reset():
                                reset_btn.disable()
                                reset_spinner.classes(remove='hidden')
                                try:
                                    reset_password(reset_user.value.strip(), reset_email.value.strip(), reset_pass.value)
                                    ui.notify('Password updated!', type='positive', position='top')
                                    tabs.set_value(login_tab)
                                except Exception as e:
                                    print(f"Reset password error: {e}")
                                    ui.notify('Reset failed.', type='negative', position='top')
                                finally:
                                    reset_btn.enable()
                                    reset_spinner.classes(add='hidden')

                            reset_btn.on_click(handle_reset)
                            reset_pass.on('keydown.enter', handle_reset)

                # Footer
                ui.label('Designed by Apostle').classes(
                    'text-[11px] font-bold uppercase tracking-[0.25em] text-gray-400 text-center mt-4'
                )


# ROUTES
pages = ui.sub_pages(routes={
    '/': login_page,
    '/login': login_page,
    '/home': protected_home,
    '/teacher': protected_teacher,
    '/insert': protected_insert,
    '/lower': lower_page,
})

pages.classes('w-full')


# RUN APP
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="School Report System",
        storage_secret='some_long_random_string_here'
    )
