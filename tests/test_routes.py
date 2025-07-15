from flask import url_for

def test_index_page(client):
    response = client.get(url_for('main.index'))
    print(f"\nDEBUG: test_index_page response data: {response.data}")
    assert response.status_code == 200
    assert b"ARUNA MOMENT" in response.data

def test_login_page(client):
    response = client.get(url_for('auth.login'))
    print(f"\nDEBUG: test_login_page response data: {response.data}")
    assert response.status_code == 200
    assert b"Login" in response.data

def test_register_page(client):
    response = client.get(url_for('auth.register'))
    print(f"\nDEBUG: test_register_page response data: {response.data}")
    assert response.status_code == 200
    assert b"Register" in response.data

def test_client_dashboard_redirect_unauthenticated(client):
    response = client.get(url_for('client.dashboard'), follow_redirects=True)
    print(f"\nDEBUG: test_client_dashboard_redirect_unauthenticated response data: {response.data}")
    assert response.status_code == 200
    assert b"Login" in response.data  # Should redirect to login page

def test_admin_panel_redirect_unauthenticated(client):
    response = client.get(url_for('admin.admin_panel'), follow_redirects=True)
    print(f"\nDEBUG: test_admin_panel_redirect_unauthenticated response data: {response.data}")
    assert response.status_code == 200
    assert b"Login" in response.data  # Should redirect to login page

def test_client_login_and_dashboard(client, test_user):
    response = client.post(url_for('auth.login'), data={
        'username': test_user.username,
        'password': 'password123'
    }, follow_redirects=True)
    print(f"\nDEBUG: test_client_login_and_dashboard response data: {response.data}")
    assert response.status_code == 200
    assert b"Dashboard Klien" in response.data  # Assuming this text is on the client dashboard

def test_admin_login_and_panel(client, admin_user):
    response = client.post(url_for('auth.login'), data={
        'username': admin_user.username,
        'password': 'adminpassword'
    }, follow_redirects=True)
    print(f"\nDEBUG: test_admin_login_and_panel response data: {response.data}")
    assert response.status_code == 200
    assert b"Dashboard Admin" in response.data  # Assuming this text is on the admin panel