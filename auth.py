"""
HaberMetrik - Kimlik Doğrulama Yardımcıları
"""

from functools import wraps
from flask import session, redirect, url_for, flash
from database import get_user_by_id


def login_required(f):
    """Giriş gerektirir decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Admin yetkisi gerektirir decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'error')
            return redirect(url_for('login'))
        
        user = get_user_by_id(session['user_id'])
        if not user or user['role'] != 'admin':
            flash('Bu sayfayı görüntülemek için admin yetkisi gereklidir.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Mevcut kullanıcıyı getir"""
    if 'user_id' in session:
        return get_user_by_id(session['user_id'])
    return None


def is_admin():
    """Kullanıcı admin mi?"""
    user = get_current_user()
    return user and user['role'] == 'admin'
