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

    # You can remove this line if you do not need admin_account
    "admin_account": "password1234",
}

# Used for case-insensitive admin login.
ADMIN_LOOKUP = {
    username.strip().lower(): password
    for username, password in ADMIN_ACCOUNTS.items()
}


def is_admin_username(username: str) -> bool:
    """
    Checks whether the username belongs to an admin account.
    This check is case-insensitive.
    """
    if not username:
        return False

    return username.strip().lower() in ADMIN_LOOKUP


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticates a user.

    1. First checks hardcoded ADMIN_ACCOUNTS.
    2. Then checks the database using verify_user().
    """
    if not username or not password:
        return False

    username_key = username.strip().lower()

    # 1) Hardcoded admin login
    if username_key in ADMIN_LOOKUP and ADMIN_LOOKUP[username_key] == password:
        return True

    # 2) Database login
    try:
        return bool(verify_user(username.strip(), password))
    except Exception as e:
        print(f"verify_user error: {e}")
        return False


# ============================================================
# LOGIN ACTIVITY LOG
# ============================================================
def update_login_activity(username, status='Active'):
    """
    Records user login events and activity status in the database.
    """
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
# GLOBAL UI SETTINGS
# ============================================================
ui.colors(primary='#14532d', secondary='#ffffff', accent='#f59e0b')


# ============================================================
# CUSTOM UI ANIMATIONS / THEME
# ============================================================
ui.add_css('''
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(26px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-fade-in-up {
    animation: fadeInUp 0.7s ease-out both;
}

@keyframes floatSoft {
    0%, 100% {
        transform: translateY(0px) scale(1);
    }
    50% {
        transform: translateY(-18px) scale(1.04);
    }
}

.animate-float-slow {
    animation: floatSoft 9s ease-in-out infinite;
}

/* Notifications */
.q-notification {
    border-radius: 18px !important;
    max-width: calc(100vw - 24px) !important;
}

.q-notification--positive {
    background: #f59e0b !important;
    color: #14532d !important;
}

.q-notification--negative,
.q-notification--warning {
    background: #14532d !important;
    color: #ffffff !important;
}

/* Scoped auth card styles */
.auth-card .primary-tabs .q-tabs__content {
    background: #f0fdf4;
    padding: 5px;
    border-radius: 20px;
    gap: 5px;
    width: 100%;
}

.auth-card .primary-tabs .q-tab {
    flex: 1 1 0;
    min-width: 0;
    border-radius: 16px;
    color: #14532d;
    text-transform: none;
    font-weight: 800;
    min-height: 48px;
    padding: 0 8px;
}

.auth-card .primary-tabs .q-tab__label {
    font-size: 12px;
    letter-spacing: .05em;
    white-space: nowrap;
}

.auth-card .primary-tabs .q-tab--active {
    background-color: #14532d !important;
    color: #ffffff !important;
}

.auth-card .primary-tabs .q-tab--active .q-tab__label {
    color: #ffffff !important;
}

.auth-card .primary-tabs .q-tab__indicator {
    display: none !important;
}

/* Inputs */
.auth-card .q-field--outlined .q-field__control {
    border-radius: 18px !important;
    min-height: 56px !important;
    background-color: #ffffff !important;
    padding: 0 16px !important;
}

.auth-card .q-field--outlined .q-field__control:before {
    border: 2px solid #dcfce7 !important;
    border-radius: 18px !important;
}

.auth-card .q-field--outlined.q-field--focused .q-field__control:after {
    border: 2px solid #f59e0b !important;
    border-radius: 18px !important;
}

.auth-card .q-field__label {
    color: #64748b !important;
}

.auth-card .q-field--focused .q-field__label {
    color: #14532d !important;
}

.auth-card .q-field__native,
.auth-card .q-field__input {
    color: #14532d !important;
    font-size: 16px !important;
}

.auth-card input {
    font-size: 16px !important;
}

.auth-card input::placeholder {
    color: #94a3b8 !important;
    opacity: 1 !important;
    font-size: 15px !important;
}

/* Buttons */
.auth-card .btn-sun {
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%) !important;
    color: #14532d !important;
    border-radius: 18px !important;
    min-height: 56px !important;
    box-shadow: 0 16px 30px -18px rgba(245, 158, 11, 0.8) !important;
    text-transform: none !important;
}

.auth-card .btn-sun:hover {
    filter: brightness(1.03);
    transform: translateY(-1px);
}

.auth-card .btn-sun:active {
    transform: translateY(0);
}

.auth-card .btn-sun .q-btn__content {
    color: #14532d !important;
    font-weight: 900;
}

.auth-card .btn-sun:disabled {
    opacity: .7;
}

/* Tab panels */
.auth-card .q-tab-panels {
    background: transparent !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}

.auth-card .q-tab-panel {
    background: transparent !important;
    padding: 0 !important;
}

/* Larger screens */
@media (min-width: 768px) {
    .auth-card .primary-tabs .q-tabs__content {
        padding: 6px;
        border-radius: 22px;
        gap: 6px;
    }

    .auth-card .primary-tabs .q-tab {
        min-height: 50px;
        border-radius: 18px;
        padding: 0 14px;
    }

    .auth-card .primary-tabs .q-tab__label {
        font-size: 13px;
    }

    .auth-card .btn-sun {
        border-radius: 20px !important;
    }
}
''')


# ============================================================
# SIMPLE REDIRECT HELPERS
# ============================================================
def redirect_to_login():
    ui.label('Redirecting to login...').classes('text-lg font-semibold')
    ui.timer(0.1, lambda: ui.navigate.to('/login'), once=True)


def redirect_to_teacher():
    ui.label('Redirecting to teacher page...').classes('text-lg font-semibold')
    ui.timer(0.1, lambda: ui.navigate.to('/teacher'), once=True)


# ============================================================
# PROTECTED PAGE WRAPPERS
# ============================================================
def protected_home():
    """
    Protects /home.
    Only logged-in admins should access this page.
    """
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
    """
    Protects /teacher.
    Any logged-in user can access this page.
    """
    if not app.storage.user.get('logged_in'):
        redirect_to_login()
        return

    teacher_page.teacher()


def protected_insert():
    """
    Protects /insert.
    Any logged-in user can access this page.
    """
    if not app.storage.user.get('logged_in'):
        redirect_to_login()
        return

    insert()


def lower_page():
    """
    Wrapper for the lower page.
    """
    target = getattr(lower, 'lower', None)

    if callable(target):
        target()
    elif callable(lower):
        lower()
    else:
        ui.label('Lower page is not configured correctly.').classes('text-lg font-semibold')


# ============================================================
# REDESIGNED LOGIN PAGE
# Mobile-friendly dark green, white, and warm amber design
# ============================================================
def login_page():
    with ui.element('div').classes(
        'fixed inset-0 h-screen w-screen overflow-y-auto overflow-x-hidden bg-[#f8fafc]'
    ):
        # Soft background decorations
        ui.element('div').classes(
            'pointer-events-none absolute -left-40 -top-40 h-[420px] w-[420px] '
            'rounded-full bg-[#14532d]/10 blur-3xl'
        )

        ui.element('div').classes(
            'pointer-events-none absolute -right-40 top-1/3 h-[520px] w-[520px] '
            'rounded-full bg-[#f59e0b]/20 blur-3xl'
        )

        ui.element('div').classes(
            'pointer-events-none absolute bottom-[-120px] left-1/3 h-[360px] w-[360px] '
            'rounded-full bg-[#14532d]/10 blur-3xl'
        )

        # Main centered content
        with ui.column().classes(
            'relative z-10 min-h-screen w-full items-center justify-center '
            'p-4 pb-16 md:p-8 md:pb-10'
        ):
            with ui.card().classes(
                'auth-card w-full max-w-5xl rounded-3xl md:rounded-[36px] '
                'border border-[#14532d]/10 bg-white shadow-2xl shadow-[#14532d]/15 '
                'overflow-hidden animate-fade-in-up'
            ).tight():

                with ui.row().classes('w-full m-0 gap-0 items-stretch'):

                    # ============================================================
                    # LEFT VISUAL PANEL - hidden on mobile
                    # ============================================================
                    with ui.column().classes(
                        'hidden md:flex w-full md:w-2/5 bg-[#14532d] relative overflow-hidden '
                        'p-10 xl:p-12'
                    ):
                        # Decorative shapes
                        ui.element('div').classes(
                            'pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full '
                            'bg-[#f59e0b]/25 blur-3xl animate-float-slow'
                        )

                        ui.element('div').classes(
                            'pointer-events-none absolute -bottom-24 -left-24 h-80 w-80 rounded-full '
                            'border-[26px] border-white/10 animate-float-slow'
                        ).style('animation-delay: 2s;')

                        ui.element('div').classes(
                            'pointer-events-none absolute right-10 top-1/3 h-14 w-14 rotate-12 '
                            'rounded-2xl bg-white/10'
                        )

                        ui.element('div').classes(
                            'pointer-events-none absolute bottom-24 right-16 h-8 w-8 rounded-full '
                            'bg-[#f59e0b]'
                        )

                        with ui.column().classes(
                            'relative z-10 h-full w-full justify-between gap-10'
                        ):
                            with ui.column().classes('gap-7'):
                                with ui.row().classes('items-center gap-4'):
                                    with ui.element('div').classes(
                                        'flex h-16 w-16 items-center justify-center rounded-[22px] '
                                        'bg-[#f59e0b] shadow-xl shadow-black/20'
                                    ):
                                        ui.icon('school').classes('text-4xl text-[#14532d]')

                                    with ui.column().classes('gap-1'):
                                        ui.label('School Portal').classes(
                                            'text-2xl font-extrabold text-white'
                                        )
                                        ui.label('Bright tools for teachers').classes(
                                            'text-[10px] font-bold uppercase tracking-[0.28em] '
                                            'text-[#f59e0b]'
                                        )

                                ui.label(
                                    'A friendly, organised place to manage lessons, pupils, '
                                    'and school updates without the clutter.'
                                ).classes('text-base leading-relaxed text-white/80')

                                with ui.column().classes('gap-3'):
                                    with ui.row().classes(
                                        'items-center gap-3 rounded-2xl border border-white/10 '
                                        'bg-white/5 px-4 py-3 backdrop-blur-sm'
                                    ):
                                        ui.icon('menu_book').classes('text-xl text-[#f59e0b]')
                                        ui.label('Lesson-ready workspace').classes(
                                            'text-sm font-semibold text-white'
                                        )

                                    with ui.row().classes(
                                        'items-center gap-3 rounded-2xl border border-white/10 '
                                        'bg-white/5 px-4 py-3 backdrop-blur-sm'
                                    ):
                                        ui.icon('groups').classes('text-xl text-[#f59e0b]')
                                        ui.label('Easy class communication').classes(
                                            'text-sm font-semibold text-white'
                                        )

                                    with ui.row().classes(
                                        'items-center gap-3 rounded-2xl border border-white/10 '
                                        'bg-white/5 px-4 py-3 backdrop-blur-sm'
                                    ):
                                        ui.icon('stars').classes('text-xl text-[#f59e0b]')
                                        ui.label('Celebrate learning every day').classes(
                                            'text-sm font-semibold text-white'
                                        )

                            with ui.row().classes('items-center gap-3'):
                                ui.element('div').classes('h-1.5 w-14 rounded-full bg-[#f59e0b]')
                                ui.element('div').classes('h-1.5 w-8 rounded-full bg-white/35')
                                ui.element('div').classes('h-1.5 w-3 rounded-full bg-white/20')

                    # ============================================================
                    # RIGHT FORM PANEL
                    # ============================================================
                    with ui.column().classes(
                        'w-full md:w-3/5 bg-white p-5 sm:p-8 md:p-10 xl:p-12'
                    ):
                        with ui.column().classes('w-full max-w-[520px] mx-auto'):

                            # Mobile header
                            with ui.column().classes('mb-8 items-center md:hidden'):
                                with ui.element('div').classes(
                                    'mb-4 flex h-16 w-16 items-center justify-center rounded-[22px] '
                                    'bg-[#14532d] shadow-lg'
                                ):
                                    ui.icon('school').classes('text-3xl text-[#f59e0b]')

                                ui.label('School Portal').classes(
                                    'text-2xl font-extrabold text-[#14532d] text-center'
                                )

                                ui.label('Bright, simple access for teachers').classes(
                                    'text-sm text-slate-500 text-center mt-1'
                                )

                            # Desktop header
                            with ui.column().classes('mb-8 hidden md:block'):
                                with ui.row().classes(
                                    'w-fit items-center gap-2 rounded-full border border-[#f59e0b]/40 '
                                    'bg-[#fffbeb] px-4 py-2'
                                ):
                                    ui.icon('wb_sunny').classes('text-lg text-[#f59e0b]')
                                    ui.label('Primary teacher friendly login').classes(
                                        'text-[10px] font-extrabold uppercase tracking-[0.22em] '
                                        'text-[#14532d]'
                                    )

                                ui.label('Welcome back').classes(
                                    'mt-5 text-3xl font-extrabold text-[#14532d]'
                                )

                                ui.label('Sign in to continue to your classroom workspace.').classes(
                                    'mt-2 text-sm text-slate-500'
                                )

                            # Tabs
                            with ui.tabs().classes(
                                'primary-tabs w-full mb-6'
                            ) as tabs:
                                login_tab = ui.tab('login', label='Login').classes('flex-1')
                                register_tab = ui.tab('register', label='Register').classes('flex-1')
                                reset_tab = ui.tab('reset', label='Reset').classes('flex-1')

                            with ui.tab_panels(tabs, value=login_tab).classes(
                                'w-full bg-transparent'
                            ):

                                # ============================================================
                                # LOGIN TAB
                                # ============================================================
                                with ui.tab_panel(login_tab).classes('p-0'):
                                    with ui.column().classes('w-full gap-5'):

                                        with ui.row().classes('items-center gap-2'):
                                            with ui.element('div').classes(
                                                'flex h-8 w-8 items-center justify-center rounded-xl '
                                                'bg-[#14532d]/5 border border-[#14532d]/10'
                                            ):
                                                ui.icon('person').classes('text-base text-[#14532d]')

                                            ui.label('Username').classes(
                                                'text-xs font-extrabold uppercase tracking-widest '
                                                'text-[#14532d]/70'
                                            )

                                        username_input = ui.input().classes('w-full').props(
                                            'outlined dense rounded placeholder="Enter your username" '
                                            'hide-bottom-space'
                                        )

                                        with ui.row().classes('items-center gap-2 mt-2'):
                                            with ui.element('div').classes(
                                                'flex h-8 w-8 items-center justify-center rounded-xl '
                                                'bg-[#14532d]/5 border border-[#14532d]/10'
                                            ):
                                                ui.icon('lock').classes('text-base text-[#14532d]')

                                            ui.label('Password').classes(
                                                'text-xs font-extrabold uppercase tracking-widest '
                                                'text-[#14532d]/70'
                                            )

                                        password_input = ui.input(
                                            password=True,
                                            password_toggle_button=True
                                        ).classes('w-full').props(
                                            'outlined dense rounded placeholder="Enter your password" '
                                            'hide-bottom-space'
                                        )

                                        with ui.row().classes('w-full justify-end -mt-1'):
                                            ui.link(
                                                'Forgot password?',
                                                '#'
                                            ).on(
                                                'click',
                                                lambda: tabs.set_value(reset_tab)
                                            ).classes(
                                                'text-xs font-bold text-[#14532d] '
                                                'hover:text-[#f59e0b] transition-colors cursor-pointer'
                                            )

                                        with ui.button().classes(
                                            'btn-sun w-full justify-center items-center gap-2'
                                        ).props('unelevated no-caps') as login_btn:
                                            login_spinner = ui.spinner(
                                                size='sm',
                                                color='primary'
                                            ).classes('hidden')

                                            ui.label('Sign in').classes(
                                                'text-sm font-black tracking-wide'
                                            )

                                        with ui.row().classes(
                                            'w-full justify-center items-center gap-2 mt-3'
                                        ):
                                            ui.label('New here?').classes(
                                                'text-xs font-semibold text-slate-400'
                                            )

                                            ui.link(
                                                'Create an account',
                                                '#'
                                            ).on(
                                                'click',
                                                lambda: tabs.set_value(register_tab)
                                            ).classes(
                                                'text-xs font-black text-[#14532d] '
                                                'hover:text-[#f59e0b] transition-colors cursor-pointer'
                                            )

                                    async def handle_page():
                                        username = username_input.value.strip()
                                        password = password_input.value

                                        # Validate empty fields
                                        if not username or not password:
                                            ui.notify('Please fill the fields', type='warning', position='top')
                                            return

                                        # Show loading state
                                        login_btn.disable()
                                        login_spinner.classes(remove='hidden')

                                        try:
                                            authenticated = authenticate_user(username, password)

                                            if authenticated:
                                                admin_user = is_admin_username(username)

                                                # Save login state
                                                app.storage.user['logged_in'] = True
                                                app.storage.user['current_user'] = username
                                                app.storage.user['username'] = username
                                                app.storage.user['name'] = username
                                                app.storage.user['is_admin'] = admin_user

                                                # Record login activity
                                                update_login_activity(username, 'Active')

                                                ui.notify('Login successful!', type='positive', position='top')

                                                # Role-based routing
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

                                # ============================================================
                                # REGISTER TAB
                                # ============================================================
                                with ui.tab_panel(register_tab).classes('p-0'):
                                    with ui.column().classes('w-full gap-5'):

                                        with ui.row().classes('items-center gap-2'):
                                            with ui.element('div').classes(
                                                'flex h-8 w-8 items-center justify-center rounded-xl '
                                                'bg-[#14532d]/5 border border-[#14532d]/10'
                                            ):
                                                ui.icon('person').classes('text-base text-[#14532d]')

                                            ui.label('Create Username').classes(
                                                'text-xs font-extrabold uppercase tracking-widest '
                                                'text-[#14532d]/70'
                                            )

                                        reg_user = ui.input().classes('w-full').props(
                                            'outlined dense rounded placeholder="Choose a username" '
                                            'hide-bottom-space'
                                        )

                                        with ui.row().classes('items-center gap-2 mt-2'):
                                            with ui.element('div').classes(
                                                'flex h-8 w-8 items-center justify-center rounded-xl '
                                                'bg-[#14532d]/5 border border-[#14532d]/10'
                                            ):
                                                ui.icon('email').classes('text-base text-[#14532d]')

                                            ui.label('Email Address').classes(
                                                'text-xs font-extrabold uppercase tracking-widest '
                                                'text-[#14532d]/70'
                                            )

                                        reg_email = ui.input().classes('w-full').props(
                                            'outlined dense rounded type="email" '
                                            'placeholder="name@school.edu" hide-bottom-space'
                                        )

                                        with ui.row().classes('items-center gap-2 mt-2'):
                                            with ui.element('div').classes(
                                                'flex h-8 w-8 items-center justify-center rounded-xl '
                                                'bg-[#14532d]/5 border border-[#14532d]/10'
                                            ):
                                                ui.icon('lock').classes('text-base text-[#14532d]')

                                            ui.label('Password').classes(
                                                'text-xs font-extrabold uppercase tracking-widest '
                                                'text-[#14532d]/70'
                                            )

                                        reg_pass = ui.input(
                                            password=True,
                                            password_toggle_button=True
                                        ).classes('w-full').props(
                                            'outlined dense rounded placeholder="Create a password" '
                                            'hide-bottom-space'
                                        )

                                        with ui.button().classes(
                                            'btn-sun w-full justify-center items-center gap-2 mt-2'
                                        ).props('unelevated no-caps') as reg_btn:
                                            reg_spinner = ui.spinner(
                                                size='sm',
                                                color='primary'
                                            ).classes('hidden')

                                            ui.label('Create Account').classes(
                                                'text-sm font-black tracking-wide'
                                            )

                                        with ui.row().classes(
                                            'w-full justify-center items-center gap-2 mt-3'
                                        ):
                                            ui.label('Already have an account?').classes(
                                                'text-xs font-semibold text-slate-400'
                                            )

                                            ui.link(
                                                'Sign in',
                                                '#'
                                            ).on(
                                                'click',
                                                lambda: tabs.set_value(login_tab)
                                            ).classes(
                                                'text-xs font-black text-[#14532d] '
                                                'hover:text-[#f59e0b] transition-colors cursor-pointer'
                                            )

                                    async def handle_registration():
                                        if not reg_user.value or not reg_email.value or not reg_pass.value:
                                            ui.notify('All fields are required!', type='warning', position='top')
                                            return

                                        reg_btn.disable()
                                        reg_spinner.classes(remove='hidden')

                                        try:
                                            add_user(
                                                reg_user.value.strip(),
                                                reg_pass.value,
                                                reg_email.value.strip()
                                            )

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

                                # ============================================================
                                # RESET PASSWORD TAB
                                # ============================================================
                                with ui.tab_panel(reset_tab).classes('p-0'):
                                    with ui.column().classes('w-full gap-5'):

                                        with ui.row().classes('items-center gap-2'):
                                            with ui.element('div').classes(
                                                'flex h-8 w-8 items-center justify-center rounded-xl '
                                                'bg-[#14532d]/5 border border-[#14532d]/10'
                                            ):
                                                ui.icon('person').classes('text-base text-[#14532d]')

                                            ui.label('Username').classes(
                                                'text-xs font-extrabold uppercase tracking-widest '
                                                'text-[#14532d]/70'
                                            )

                                        reset_user = ui.input().classes('w-full').props(
                                            'outlined dense rounded placeholder="Enter your username" '
                                            'hide-bottom-space'
                                        )

                                        with ui.row().classes('items-center gap-2 mt-2'):
                                            with ui.element('div').classes(
                                                'flex h-8 w-8 items-center justify-center rounded-xl '
                                                'bg-[#14532d]/5 border border-[#14532d]/10'
                                            ):
                                                ui.icon('email').classes('text-base text-[#14532d]')

                                            ui.label('Email Address').classes(
                                                'text-xs font-extrabold uppercase tracking-widest '
                                                'text-[#14532d]/70'
                                            )

                                        reset_email = ui.input().classes('w-full').props(
                                            'outlined dense rounded type="email" '
                                            'placeholder="name@school.edu" hide-bottom-space'
                                        )

                                        with ui.row().classes('items-center gap-2 mt-2'):
                                            with ui.element('div').classes(
                                                'flex h-8 w-8 items-center justify-center rounded-xl '
                                                'bg-[#14532d]/5 border border-[#14532d]/10'
                                            ):
                                                ui.icon('key').classes('text-base text-[#14532d]')

                                            ui.label('New Password').classes(
                                                'text-xs font-extrabold uppercase tracking-widest '
                                                'text-[#14532d]/70'
                                            )

                                        reset_pass = ui.input(
                                            password=True,
                                            password_toggle_button=True
                                        ).classes('w-full').props(
                                            'outlined dense rounded placeholder="Enter new password" '
                                            'hide-bottom-space'
                                        )

                                        with ui.button().classes(
                                            'btn-sun w-full justify-center items-center gap-2 mt-2'
                                        ).props('unelevated no-caps') as reset_btn:
                                            reset_spinner = ui.spinner(
                                                size='sm',
                                                color='primary'
                                            ).classes('hidden')

                                            ui.label('Reset Password').classes(
                                                'text-sm font-black tracking-wide'
                                            )

                                        with ui.row().classes(
                                            'w-full justify-center items-center gap-2 mt-3'
                                        ):
                                            ui.label('Remembered your password?').classes(
                                                'text-xs font-semibold text-slate-400'
                                            )

                                            ui.link(
                                                'Back to Login',
                                                '#'
                                            ).on(
                                                'click',
                                                lambda: tabs.set_value(login_tab)
                                            ).classes(
                                                'text-xs font-black text-[#14532d] '
                                                'hover:text-[#f59e0b] transition-colors cursor-pointer'
                                            )

                                    async def handle_reset():
                                        reset_btn.disable()
                                        reset_spinner.classes(remove='hidden')

                                        try:
                                            reset_password(
                                                reset_user.value.strip(),
                                                reset_email.value.strip(),
                                                reset_pass.value
                                            )

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

            # Footer below the card so it does not overlap mobile content
            ui.label('Designed by Apostle').classes(
                'mt-6 text-center text-[10px] md:text-[11px] font-bold uppercase '
                'tracking-[0.25em] text-[#14532d]/35'
            )


# ============================================================
# ROUTES
# ============================================================
pages = ui.sub_pages(routes={
    '/': login_page,
    '/login': login_page,
    '/home': protected_home,
    '/teacher': protected_teacher,
    '/insert': protected_insert,
    '/lower': lower_page,
})

# Force the router container to occupy full width
pages.classes('w-full')


# ============================================================
# RUN APP
# ============================================================
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="School Report System",
        storage_secret='some_long_random_string_here'
    )
