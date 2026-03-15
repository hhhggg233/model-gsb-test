from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import User
from extensions import db
from utils import get_cached_persons, cache_persons, invalidate_persons_cache

persons_bp = Blueprint('persons', __name__)

@persons_bp.route('/api/persons', methods=['GET'])
@login_required
def get_persons():
    cached = get_cached_persons()
    if cached:
        return jsonify(cached)
    
    persons = User.query.filter(User.age.isnot(None), User.position.isnot(None)).all()
    persons_list = [{
        'id': p.id,
        'name': p.username,
        'age': p.age,
        'position': p.position
    } for p in persons]
    cache_persons(persons_list)
    return jsonify(persons_list)

@persons_bp.route('/api/persons', methods=['POST'])
@login_required
def add_person():
    if not current_user.is_admin():
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if User.query.filter_by(username=data['name']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    default_email = f"{data['name'].lower()}@example.com"
    person = User(
        username=data['name'],
        email=data.get('email', default_email),
        age=data['age'],
        position=data['position']
    )
    person.set_password(data.get('password', '123456'))
    db.session.add(person)
    db.session.commit()
    invalidate_persons_cache()
    return jsonify({
        'id': person.id,
        'name': person.username,
        'age': person.age,
        'position': person.position
    }), 201

@persons_bp.route('/api/persons/<int:person_id>', methods=['PUT'])
@login_required
def update_person(person_id):
    if not current_user.is_admin():
        return jsonify({'error': 'Permission denied'}), 403
    
    person = User.query.get_or_404(person_id)
    data = request.get_json()
    person.username = data['name']
    person.age = data['age']
    person.position = data['position']
    db.session.commit()
    invalidate_persons_cache()
    return jsonify({
        'id': person.id,
        'name': person.username,
        'age': person.age,
        'position': person.position
    })

@persons_bp.route('/api/persons/<int:person_id>', methods=['DELETE'])
@login_required
def delete_person(person_id):
    if not current_user.is_admin():
        return jsonify({'error': 'Permission denied'}), 403
    
    person = User.query.get_or_404(person_id)
    db.session.delete(person)
    db.session.commit()
    invalidate_persons_cache()
    return jsonify({'message': 'Person deleted successfully'})
