# Code from http://cork.firelet.net/howto.html
# and  from http://cork.firelet.net/example_webapp.html

from sys import stderr

import bottle
from bottle import post, request, route, run
from beaker.middleware import SessionMiddleware
from cork import Cork
from cork.backends import SQLiteBackend


# Globals
sqliteBackend = None
backend = None
app = None


# Set up
def setup():
    # JSON backend for now
    global sqliteBackend
    sqliteBackend = SQLiteBackend(filename='SQLiteDB.db',
                                  users_tname='user_table',
                                  roles_tname='role_table',
                                  pending_reg_tname='register_table',
                                  initialize=False)
    global backend
    backend = Cork(backend=sqliteBackend)

    # Session
    global app
    app = bottle.app()
    config = {
        'session.encrypt_key': '+9#uc(Xcb2!G?44',
        'session.type': 'cookie',
        'session.validate_key': True,
    }
    app = SessionMiddleware(wrap_app=app, config=config)
# End of setup


# Get information from POST request
def post_get(name, default=''):
    return request.POST.get(name, default).strip()
# End of post_get


# Home Page
@route('/')
def home():
    backend.require(fail_redirect='/login')
# End of home


# Login
@post('/login')
def login():
    username = post_get('username')
    password = post_get('password')
    backend.login(username=username, password=password,
                  success_redirect='/login_success',
                  fail_redirect='/login_failed')
# End of login


# Successful login
@route('/login_success')
def login_success():
    return 'Successfully logged in.'
# End of success


# Failed login
@route('/login_failed')
def login_failed():
    return 'Incorrect username or password.'
# End of failed


# Logout
@route('/logout')
def logout():
    backend.logout(success_redirect='/login', fail_redirect='/login')
# End of logout


# List roles
@route('/role')
def list_roles():
    backend.require(role='admin', fixed_role=True,
                    fail_redirect='/insufficient_perms')
    # Build dictionary
    l = []
    for role in backend.list_roles():
        role_dict = {
            'id': role[0],
            'level': role[1]
         }
        l.append(role_dict)
    return {'role': l}
# End of list_roles


# Create role
@post('/create_role')
def create_role():
    # Require admin role
    backend.require(role='admin', fixed_role=True,
                    fail_redirect='/insufficient_perms')

    # Get params from form
    role = post_get('role')
    level = post_get('level')

    # If role already exists, stop
    exists = False
    for curr_role in backend.list_roles():
        if role == curr_role[0]:
            exists = True
            break
    if exists:
        return 'Failed: role ' + role + ' already exists.'

    # Create user
    backend.create_role(role, level)
    sqliteBackend.connection.commit()
    return 'Success.'

# List users
@route('/user')
def list_users():
    backend.require(role='admin', fixed_role=True,
                    fail_redirect='/insufficient_perms')

    # Build dictionary
    generator = backend.list_users()
    l = []
    for user in generator:
        user_dict = {
            'id': user[0],
            'role': user[1],
            'email': user[2],
            'desc': user[3]
        }
        l.append(user_dict)
    return {'user': l}
# End of list_users


# Create user
@post('/create_user')
def create_user():
    # Require admin role
    backend.require(role='admin', fixed_role=True,
                    fail_redirect='/insufficient_perms')

    # Get params from form
    username = post_get('username')
    role = post_get('role')
    email = post_get('email')
    password = post_get('password')

    # If user already exists, stop
    if backend.user(username) is not None:
        return 'Failed: user ' + username + ' already exists.'

    # Ensure role exists
    valid_role = False
    for curr_role in backend.list_roles():
        if role == curr_role[0]:
            valid_role = True
            break
    if not valid_role:
        return 'Failed: ' + role + ' is not a valid role.'

    # Create user
    backend.create_user(username=username, role=role, email_addr=email,
                        password=password)
    sqliteBackend.connection.commit()
    return 'Success.'
# End of create_user


# Delete user
@post('/delete_user')
def delete_user():
    # Require admin role
    backend.require(role='admin', fixed_role=True,
                    fail_redirect='/insufficient_perms')

    # Get params from form
    username = post_get('username')

    # Do not allow deleting original admin user
    if username == 'admin':
        return 'Failed: unable to delete original admin user.'

    # If user does not exist, stop
    if backend.user(username) is None:
        return 'Failed: user ' + username + ' does not exist.'

    # Delete user
    backend.delete_user(username)
    sqliteBackend.connection.commit()
    return 'Success.'
# End of delete_user


# Static pages
# Static Login Page
@route('/login')
def login_page():
    return '<form action="/login" method="post">' \
           '    <input type="text" id="username" name="username">' \
           '    <input type="password" id="password" name="password">' \
           '    <input type="submit" value="Login">'
# End of login_page


# Static Insufficient Permissions Page
@route('/insufficient_perms')
def insufficient_perms_page():
    return "Insufficient permissions"
# End of insufficient_perms_page


# Static Create Role Page
@route('/create_role')
def create_role_page():
    backend.require(role='admin', fixed_role=True,
                    fail_redirect='/insufficient_perms')
    return '<form action="/create_role" method="post">' \
           '    <label for="role">Role: </label>' \
           '    <input type="text" id="role" name="role">' \
           '    <br>' \
           '    <label for="level">Level: </label>' \
           '    <input type="text" id="level" name="level">' \
           '    <br>' \
           '    <input type="submit" value="Create">'
# End of create_user_page


# Static Create User Page
@route('/create_user')
def create_user_page():
    backend.require(role='admin', fixed_role=True,
                    fail_redirect='/insufficient_perms')
    return '<form action="/create_user" method="post">' \
           '    <label for="username">Username: </label>' \
           '    <input type="text" id="username" name="username">' \
           '    <br>' \
           '    <label for="role">Role: </label>' \
           '    <input type="text" id="role" name="role">' \
           '    <br>' \
           '    <label for="email">Email: </label>' \
           '    <input type="text" id="email" name="email">' \
           '    <br>' \
           '    <label for="password">Password: </label>' \
           '    <input type="password" id="password" name="password">' \
           '    <br>' \
           '    <input type="submit" value="Create">'
# End of create_user_page


# Static Delete User Page
@route('/delete_user')
def delete_user_page():
    backend.require(role='admin', fixed_role=True,
                    fail_redirect='/insufficient_perms')
    return '<form action="/delete_user" method="post">' \
           '    <label for="username">Username: </label>' \
           '    <input type="text" id="username" name="username">' \
           '    <br>' \
           '    <input type="submit" value="Delete">'


# Main function
def main():
    # Setup
    setup()

    # Run bottle
    run(app=app, host='localhost', port=8080, debug=True)
# End of main

if __name__ == "__main__":
    main()