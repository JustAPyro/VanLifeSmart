from .models import User

def get_admin():
    return User(
        email='luke.m.hanna@gmail.com',
        password='7x43tyzQ@k',
        name='Luke'
    )
