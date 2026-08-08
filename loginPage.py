from verifying_passcode import verify_user, add_user, reset_password, get_db_connection
from nicegui import ui, app
import school_home_page
import teacher_page
import lower
from insert import insert
from datetime import datetime



# ADMIN ACCOUNTS

ADMIN_ACCOUNTS = {
    "Apostle": "password1234",
    "Principal": "AdminPass2026",
    "Headmaster": "Secret123",

    # You can remove this line if you do not need admin_account
    "admin_account": "password1234",
}

# Used for case-insensitive admin login.
# Example: "apostle", "Apostle", "APOSTLE" will all match.
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

    If you want only database users, remove the hardcoded admin check.
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

        # Ensure the activity logs table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT, 
                timestamp TEXT,
                status TEXT
            )
        ''')

        # If a new active login happens, mark previous active sessions as inactive
        if status == 'Active':
            cursor.execute("""
                UPDATE activity_logs
                SET status = 'Inactive'
                WHERE status = 'Active'
            """)

        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Insert the new login activity record
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
ui.colors(primary='#800000', secondary='#ffffff', accent='#f59e0b')


# ============================================================
# CUSTOM UI ANIMATIONS
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

@keyframes floatSlow {
    0%, 100% {
        transform: translateY(0px) scale(1);
    }
    50% {
        transform: translateY(-18px) scale(1.04);
    }
}

.animate-float-slow {
    animation: floatSlow 9s ease-in-out infinite;
}

@keyframes glowPulse {
    0%, 100% {
        opacity: 0.55;
    }
    50% {
        opacity: 0.95;
    }
}

.animate-glow-pulse {
    animation: glowPulse 4s ease-in-out infinite;
}
''')



# SIMPLE REDIRECT HELPERS

def redirect_to_login():
    """
    Shows a small redirect message and sends the user to /login.
    """
    ui.label('Redirecting to login...').classes('text-lg font-semibold')
    ui.timer(0.1, lambda: ui.navigate.to('/login'), once=True)


def redirect_to_teacher():
    """
    Shows a small redirect message and sends the user to /teacher.
    """
    ui.label('Redirecting to teacher page...').classes('text-lg font-semibold')
    ui.timer(0.1, lambda: ui.navigate.to('/teacher'), once=True)



# PROTECTED PAGE WRAPPERS
# ===========================================================
def protected_home():
    """
    Protects /home.
    Only logged-in admins should access this page.
    """
    if not app.storage.user.get('logged_in'):
        redirect_to_login()
        return

    current_user = app.storage.user.get('current_user', '')

    # Allow access if storage says admin,
    # or if the stored current user matches an admin username.
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

    If your lower.py file contains a function called lower(),
    this will call it.

    If your lower page function has a different name,
    change this function accordingly.
    """
    target = getattr(lower, 'lower', None)

    if callable(target):
        target()
    elif callable(lower):
        lower()
    else:
        ui.label('Lower page is not configured correctly.').classes('text-lg font-semibold')



# REDESIGNED LOGIN PAGE

def login_page():
    # Full-screen background
    with ui.row().classes(
        'fixed inset-0 w-screen h-screen m-0 p-0 bg-slate-950 overflow-y-auto'
    ):
        # Background gradient
        ui.element('div').classes('absolute inset-0 pointer-events-none').style(
            '''
            background:
                linear-gradient(135deg, #020617 0%, #190303 42%, #4d0000 100%);
            '''
        )

        # Decorative glowing shapes
        ui.element('div').classes(
            'absolute -top-48 -left-48 w-[520px] h-[520px] rounded-full '
            'bg-[#800000]/45 blur-3xl animate-glow-pulse pointer-events-none'
        )

        ui.element('div').classes(
            'absolute -bottom-64 -right-44 w-[620px] h-[620px] rounded-full '
            'bg-amber-500/10 blur-3xl animate-float-slow pointer-events-none'
        )

        ui.element('div').classes('absolute inset-0 pointer-events-none').style(
            '''
            background:
                radial-gradient(circle at 18% 18%, rgba(255,255,255,0.08), transparent 30%),
                radial-gradient(circle at 82% 8%, rgba(245,158,11,0.14), transparent 32%),
                radial-gradient(circle at 88% 78%, rgba(128,0,0,0.36), transparent 46%);
            '''
        )

        # Main content
        with ui.row().classes(
            'relative z-10 w-full min-h-full items-center justify-center p-4 md:p-10 gap-10'
        ):
            # Left branding panel, hidden on small screens
            with ui.column().classes(
                'hidden lg:flex flex-col items-start justify-center max-w-xl gap-7 animate-fade-in-up'
            ):
                with ui.row().classes('items-center gap-5'):
                    with ui.element('div').classes(
                        'w-20 h-20 rounded-3xl overflow-hidden ring-2 ring-amber-400/70 '
                        'shadow-2xl shadow-black/50'
                    ):
                        ui.image('badge.jpeg').classes('w-full h-full object-cover')

                    with ui.column().classes('gap-1'):
                        ui.label('Institutional Portal').classes(
                            'text-4xl font-black tracking-tight text-white'
                        )
                        ui.label('Secure Access Management').classes(
                            'text-[11px] font-bold uppercase tracking-[0.35em] text-amber-200/90'
                        )

                ui.label(
                    'Access your administrative dashboard, teacher workspace, and school '
                    'management tools from one secure entry point.'
                ).classes(
                    'text-lg leading-relaxed text-slate-200/90'
                )

                with ui.row().classes('gap-3 flex-wrap'):
                    with ui.row().classes(
                        'items-center gap-2 rounded-2xl border border-white/10 bg-white/5 '
                        'px-4 py-3 backdrop-blur'
                    ):
                        ui.icon('person').classes('text-amber-300')
                        ui.label('Role-based access').classes('text-sm font-semibold text-white')

                    with ui.row().classes(
                        'items-center gap-2 rounded-2xl border border-white/10 bg-white/5 '
                        'px-4 py-3 backdrop-blur'
                    ):
                        ui.icon('timeline').classes('text-amber-300')
                        ui.label('Activity monitoring').classes('text-sm font-semibold text-white')

                    with ui.row().classes(
                        'items-center gap-2 rounded-2xl border border-white/10 bg-white/5 '
                        'px-4 py-3 backdrop-blur'
                    ):
                        ui.icon('lock').classes('text-amber-300')
                        ui.label('Secure sessions').classes('text-sm font-semibold text-white')

            # Right login card panel
            with ui.column().classes(
                'w-full max-w-[560px] animate-fade-in-up'
            ):
                with ui.card().classes(
                    'w-full rounded-[32px] border border-white/15 bg-white/[0.97] '
                    'backdrop-blur-2xl overflow-hidden hover:shadow-2xl transition-all'
                ).tight():
                    # Top gradient strip
                    ui.element('div').classes(
                        'h-1.5 w-full bg-gradient-to-r from-[#800000] via-amber-500 to-[#800000]'
                    )

                    with ui.column().classes('w-full p-7 md:p-10'):

                        # Mobile header
                        with ui.column().classes('w-full items-center mb-8 lg:hidden'):
                            with ui.row().classes(
                                'w-16 h-16 rounded-3xl overflow-hidden mb-4 '
                                'ring-2 ring-[#800000]/20 shadow-xl'
                            ):
                                ui.image('badge.jpeg').classes('w-full h-full object-cover')

                            ui.label('Institutional Portal').classes(
                                'text-2xl font-black tracking-tight text-slate-900 text-center'
                            )

                            ui.label('Secure Access Management').classes(
                                'text-[10px] font-bold uppercase tracking-[0.28em] '
                                'text-slate-400 mt-1 text-center'
                            )

                        # Desktop header
                        with ui.column().classes('w-full mb-8 hidden lg:flex'):
                            ui.label('Welcome back').classes(
                                'text-3xl font-black tracking-tight text-slate-900'
                            )
                            ui.label('Sign in to continue to your dashboard.').classes(
                                'text-sm text-slate-500 mt-1'
                            )

                        # Tabs
                        with ui.tabs().classes(
                            'w-full rounded-2xl bg-slate-100 p-1 shadow-inner'
                        ) as tabs:
                            login_tab = ui.tab('login', label='Login').classes(
                                'flex-1 rounded-xl text-[11px] font-black uppercase tracking-wider'
                            )
                            register_tab = ui.tab('register', label='Register').classes(
                                'flex-1 rounded-xl text-[11px] font-black uppercase tracking-wider'
                            )
                            reset_tab = ui.tab('reset', label='Reset').classes(
                                'flex-1 rounded-xl text-[11px] font-black uppercase tracking-wider'
                            )

                        with ui.tab_panels(tabs, value=login_tab).classes(
                            'w-full bg-transparent mt-6'
                        ):

                            
                            # LOGIN TAB
                            
                            with ui.tab_panel(login_tab).classes('p-0'):
                                with ui.column().classes('w-full gap-4'):

                                    with ui.row().classes('items-center gap-2'):
                                        ui.icon('person').classes('text-slate-400 text-lg')
                                        ui.label('Username').classes(
                                            'text-xs font-black uppercase tracking-widest text-slate-500'
                                        )

                                    username_input = ui.input().classes('w-full').props(
                                        'outlined dense rounded placeholder="Enter your username"'
                                    )

                                    with ui.row().classes('items-center gap-2 mt-2'):
                                        ui.icon('lock').classes('text-slate-400 text-lg')
                                        ui.label('Password').classes(
                                            'text-xs font-black uppercase tracking-widest text-slate-500'
                                        )

                                    password_input = ui.input(
                                        password=True,
                                        password_toggle_button=True
                                    ).classes('w-full').props(
                                        'outlined dense rounded placeholder="Enter your password"'
                                    )

                                    with ui.row().classes('w-full justify-end -mt-1'):
                                        ui.link(
                                            'Forgot password?',
                                            '#'
                                        ).on(
                                            'click',
                                            lambda: tabs.set_value(reset_tab)
                                        ).classes(
                                            'text-xs font-semibold text-[#800000] '
                                            'hover:text-amber-600 transition-colors cursor-pointer'
                                        )

                                    with ui.button().classes(
                                        'w-full py-4 mt-2 rounded-2xl text-white font-black '
                                        'text-sm tracking-[0.18em] bg-gradient-to-r '
                                        'from-[#800000] to-[#500000] hover:from-[#6d0000] '
                                        'hover:to-[#430000] active:scale-[0.99] transition-all '
                                        'shadow-xl shadow-[#800000]/40 justify-center items-center gap-2'
                                    ).props('unelevated no-caps') as login_btn:
                                        login_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                                        ui.label('SIGN IN').classes('font-black')

                                    with ui.row().classes('w-full justify-center items-center gap-2 mt-3'):
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
                                            'text-xs font-black text-[#800000] '
                                            'hover:text-amber-600 transition-colors cursor-pointer'
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

                            
                            # REGISTER TAB
                            
                            with ui.tab_panel(register_tab).classes('p-0'):
                                with ui.column().classes('w-full gap-4'):

                                    with ui.row().classes('items-center gap-2'):
                                        ui.icon('person').classes('text-slate-400 text-lg')
                                        ui.label('Create Username').classes(
                                            'text-xs font-black uppercase tracking-widest text-slate-500'
                                        )

                                    reg_user = ui.input().classes('w-full').props(
                                        'outlined dense rounded placeholder="Choose a username"'
                                    )

                                    with ui.row().classes('items-center gap-2 mt-2'):
                                        ui.icon('email').classes('text-slate-400 text-lg')
                                        ui.label('Email Address').classes(
                                            'text-xs font-black uppercase tracking-widest text-slate-500'
                                        )

                                    reg_email = ui.input().classes('w-full').props(
                                        'outlined dense rounded type="email" '
                                        'placeholder="name@school.edu"'
                                    )

                                    with ui.row().classes('items-center gap-2 mt-2'):
                                        ui.icon('lock').classes('text-slate-400 text-lg')
                                        ui.label('Password').classes(
                                            'text-xs font-black uppercase tracking-widest text-slate-500'
                                        )

                                    reg_pass = ui.input(
                                        password=True,
                                        password_toggle_button=True
                                    ).classes('w-full').props(
                                        'outlined dense rounded placeholder="Create a password"'
                                    )

                                    with ui.button().classes(
                                        'w-full py-4 mt-4 rounded-2xl text-white font-black '
                                        'text-sm tracking-[0.18em] bg-gradient-to-r '
                                        'from-[#800000] to-[#500000] hover:from-[#6d0000] '
                                        'hover:to-[#430000] active:scale-[0.99] transition-all '
                                        'shadow-xl shadow-[#800000]/40 justify-center items-center gap-2'
                                    ).props('unelevated no-caps') as reg_btn:
                                        reg_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                                        ui.label('CREATE ACCOUNT').classes('font-black')

                                    with ui.row().classes('w-full justify-center items-center gap-2 mt-3'):
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
                                            'text-xs font-black text-[#800000] '
                                            'hover:text-amber-600 transition-colors cursor-pointer'
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

                            
                            # RESET PASSWORD TAB
                            
                            with ui.tab_panel(reset_tab).classes('p-0'):
                                with ui.column().classes('w-full gap-4'):

                                    with ui.row().classes('items-center gap-2'):
                                        ui.icon('person').classes('text-slate-400 text-lg')
                                        ui.label('Username').classes(
                                            'text-xs font-black uppercase tracking-widest text-slate-500'
                                        )

                                    reset_user = ui.input().classes('w-full').props(
                                        'outlined dense rounded placeholder="Enter your username"'
                                    )

                                    with ui.row().classes('items-center gap-2 mt-2'):
                                        ui.icon('email').classes('text-slate-400 text-lg')
                                        ui.label('Email Address').classes(
                                            'text-xs font-black uppercase tracking-widest text-slate-500'
                                        )

                                    reset_email = ui.input().classes('w-full').props(
                                        'outlined dense rounded type="email" '
                                        'placeholder="name@school.edu"'
                                    )

                                    with ui.row().classes('items-center gap-2 mt-2'):
                                        ui.icon('key').classes('text-slate-400 text-lg')
                                        ui.label('New Password').classes(
                                            'text-xs font-black uppercase tracking-widest text-slate-500'
                                        )

                                    reset_pass = ui.input(
                                        password=True,
                                        password_toggle_button=True
                                    ).classes('w-full').props(
                                        'outlined dense rounded placeholder="Enter new password"'
                                    )

                                    with ui.button().classes(
                                        'w-full py-4 mt-4 rounded-2xl text-white font-black '
                                        'text-sm tracking-[0.18em] bg-gradient-to-r '
                                        'from-[#800000] to-[#500000] hover:from-[#6d0000] '
                                        'hover:to-[#430000] active:scale-[0.99] transition-all '
                                        'shadow-xl shadow-[#800000]/40 justify-center items-center gap-2'
                                    ).props('unelevated no-caps') as reset_btn:
                                        reset_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                                        ui.label('RESET PASSWORD').classes('font-black')

                                    with ui.row().classes('w-full justify-center items-center gap-2 mt-3'):
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
                                            'text-xs font-black text-[#800000] '
                                            'hover:text-amber-600 transition-colors cursor-pointer'
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

        # Footer
        with ui.row().classes(
            'fixed bottom-5 left-0 right-0 z-20 justify-center items-center pointer-events-none'
        ):
            ui.label('Designed by Apostle').classes(
                'text-[11px] font-bold uppercase tracking-[0.25em] text-white/45'
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

# Force the router container to occupy full width
pages.classes('w-full')



# RUN APP

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="School Report System",
        storage_secret='some_long_random_string_here'
    )
