from verifying_passcode import verify_user, add_user, reset_password
from nicegui import ui, app
import school_home_page
import teacher_page
import lower
from insert import insert
import sqlite3
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

# Define the shared database constant used across the application
DB = 'School_Results_Database.db'

# Function to record user login events and activity status in the database
def update_login_activity(username, status='Active'):
    try:
        with sqlite3.connect(DB) as conn:
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
                cursor.execute("UPDATE activity_logs SET status = 'Inactive' WHERE status = 'Active'")
            
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            # Insert the new login activity record
            cursor.execute('''
                INSERT INTO activity_logs (username, timestamp, status) 
                VALUES (?, ?, ?)
            ''', (username, current_timestamp, status))
            conn.commit()
    except Exception as e:
        print(f"Activity log error: {e}")

# Custom Security Middleware to handle route protection and cache control headers
class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Prevent browser caching of protected views
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        # Protect specific backend/dashboard paths from unauthenticated access
        if request.url.path in ['/home', '/teacher', '/insert']:
            if not app.storage.user.get('logged_in'):
                return RedirectResponse('/login')
        return response

# Global application state variables
app_state = {
    'logged_in': False,
    'current_user': None
}

# Apply global color scheme to the UI components
ui.colors(primary='#800000', secondary='#ffffff', accent='#f59e0b')

# Define administrative credentials for role-based routing
ADMIN_ACCOUNTS = {
    "Apostle": "password1234",
    "Principal": "AdminPass2026",
    "Headmaster": "Secret123"
}

# Main UI layout and logic for the Authentication Portal (Login, Register, Reset)
def login_page():
    # Use fixed positioning or full viewport dimensions to eliminate scrolling white spaces
    with ui.row().classes('fixed inset-0 w-screen h-screen m-0 p-0 no-wrap bg-gradient-to-br from-slate-900 via-slate-800 to-[#500000] justify-center items-center overflow-hidden'):
        
        # Centered container for card and viewport-level footer attribution
        with ui.column().classes('items-center gap-4 relative w-full h-full justify-center'):
            
            # Centered glassmorphism-inspired container card
            with ui.card().classes('w-[460px] p-10 bg-white/95 backdrop-blur-xl shadow-2xl rounded-[28px] border border-white/20').tight():
                
                # Header Branding
                with ui.column().classes('w-full items-center mb-8'):
                    with ui.row().classes('w-14 h-14 bg-[#800000]/10 rounded-2xl justify-center items-center mb-3 shadow-inner overflow-hidden'):
                        ui.image('badge.jpeg').classes('w-full h-full object-cover')
                    ui.label('Institutional Portal').classes('text-2xl font-extrabold tracking-tight text-slate-800 text-center')
                    ui.label('Secure Access Management').classes('text-xs font-medium text-slate-400 mt-1 uppercase tracking-wider')

                # Navigation tabs switching between Login, Registration, and Password Reset
                with ui.tabs().classes('w-full bg-slate-100/80 rounded-xl p-1 shadow-inner') as tabs:
                    login_tab = ui.tab('login').classes('flex-1 text-xs font-semibold rounded-lg tracking-wide')
                    register_tab = ui.tab('Register').classes('flex-1 text-xs font-semibold rounded-lg tracking-wide')
                    reset_tab = ui.tab('Reset').classes('flex-1 text-xs font-semibold rounded-lg tracking-wide')
                    
                with ui.tab_panels(tabs, value=login_tab).classes('w-full bg-transparent mt-6'):
                    
                    # --- LOGIN TAB PANEL ---
                    with ui.tab_panel(login_tab).classes('flex flex-col gap-4 p-0'):
                        username_input = ui.input('Username').classes('w-full').props('outlined dense rounded')
                        password_input = ui.input('Password', password=True, password_toggle_button=True).classes('w-full').props('outlined dense rounded')

                        login_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                        
                        async def handle_page():
                            username = username_input.value.strip()
                            password = password_input.value
                            
                            # Validate that inputs are not empty
                            if not username or not password:
                                ui.notify('Please fill the fields', type='warning', position='top')
                                return

                            # Show loading state
                            login_btn.disable()
                            login_spinner.classes(remove='hidden')

                            try:
                                # Authenticate user against database records
                                if verify_user(username, password): 
                                    app.storage.user['logged_in'] = True
                                    app.storage.user['current_user'] = username
                                    app.storage.user['username'] = username
                                    app.storage.user['name'] = username
                                    update_login_activity(username, 'Active')
                                    
                                    ui.notify('Login successful!', type='positive', position='top')
                                    
                                    # Role-based Routing (Admins go to /home, teachers/others go to /teacher)
                                    if username in ADMIN_ACCOUNTS and ADMIN_ACCOUNTS[username] == password:
                                        ui.navigate.to('/home')
                                    else:
                                        ui.navigate.to('/teacher')
                                else:
                                    ui.notify('Invalid username or password', type='negative', position='top')
                                    login_btn.enable()
                                    login_spinner.classes(add='hidden')
                            except Exception as e:
                                ui.notify(f'An error occurred: {e}', type='negative', position='top')
                                login_btn.enable()
                                login_spinner.classes(add='hidden')

                        with ui.button(on_click=handle_page).classes('w-full py-3.5 mt-3 text-white font-bold bg-[#800000] hover:bg-[#600000] active:scale-[0.99] transition-all rounded-xl shadow-lg shadow-[#800000]/30 justify-center items-center gap-2') as login_btn:
                            login_spinner
                            ui.label('SIGN IN').classes('font-bold')

                    # --- REGISTER TAB PANEL ---
                    with ui.tab_panel(register_tab).classes('flex flex-col gap-4 p-0'):
                        reg_user = ui.input('Create Username').classes('w-full').props('outlined dense rounded')
                        reg_email = ui.input('Email Address').classes('w-full').props('outlined dense rounded')
                        reg_pass = ui.input('Password', password=True, password_toggle_button=True).classes('w-full').props('outlined dense rounded')
                        
                        reg_spinner = ui.spinner(size='sm', color='white').classes('hidden')

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
                            except:
                                ui.notify('Registration failed.', type='negative', position='top')
                            finally:
                                reg_btn.enable()
                                reg_spinner.classes(add='hidden')

                        with ui.button(on_click=handle_registration).classes('w-full py-3.5 mt-2 text-white font-bold bg-[#800000] hover:bg-[#600000] active:scale-[0.99] transition-all rounded-xl shadow-lg shadow-[#800000]/30 justify-center items-center gap-2') as reg_btn:
                            reg_spinner
                            ui.label('REGISTER').classes('font-bold')

                    # --- RESET PASSWORD TAB PANEL ---
                    with ui.tab_panel(reset_tab).classes('flex flex-col gap-4 p-0'):
                        reset_user = ui.input('Username').classes('w-full').props('outlined dense rounded')
                        reset_email = ui.input('Email Address').classes('w-full').props('outlined dense rounded')
                        reset_pass = ui.input('New Password', password=True, password_toggle_button=True).classes('w-full').props('outlined dense rounded')

                        reset_spinner = ui.spinner(size='sm', color='white').classes('hidden')

                        async def handle_reset():
                            reset_btn.disable()
                            reset_spinner.classes(remove='hidden')

                            try:
                                reset_password(reset_user.value.strip(), reset_email.value.strip(), reset_pass.value)
                                ui.notify('Password updated!', type='positive', position='top')
                                tabs.set_value(login_tab)
                            except:
                                ui.notify('Reset failed.', type='negative', position='top')
                            finally:
                                reset_btn.enable()
                                reset_spinner.classes(add='hidden')

                        with ui.button(on_click=handle_reset).classes('w-full py-3.5 mt-2 text-white font-bold bg-[#800000] hover:bg-[#600000] active:scale-[0.99] transition-all rounded-xl shadow-lg shadow-[#800000]/30 justify-center items-center gap-2') as reset_btn:
                            reset_spinner
                            ui.label('RESET PASSWORD').classes('font-bold')

                        ui.link('Back to Login', '#').on('click', lambda: tabs.set_value(login_tab)).classes('text-xs font-semibold text-slate-400 hover:text-[#800000] text-center w-full mt-3')

            # Professional SaaS viewport-level footer pinned at the bottom-center
            with ui.row().classes('absolute bottom-4 left-0 right-0 justify-center items-center pointer-events-none'):
                ui.label('Designed by Apostle').classes('text-xs font-medium text-slate-400/80 tracking-wider')

# Define application sub-pages and URL route mapping
pages = ui.sub_pages(routes={
    '/' : login_page,
    '/login' : login_page,
    '/home' : school_home_page.home,
    '/teacher': teacher_page.teacher,
    '/insert': insert,
    '/lower': lower,
})

# Force the router container to occupy full width
pages.classes('w-full') 

# Run the NiceGUI server instance
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="School Report System", storage_secret='some_long_random_string_here')
