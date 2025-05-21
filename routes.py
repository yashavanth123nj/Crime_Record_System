from flask import render_template, redirect, url_for, flash, request, jsonify, session, abort
from flask_login import login_required, current_user
from urllib.parse import urlparse
from sqlalchemy import func, extract, desc, or_
from datetime import datetime, date, timedelta
import calendar

from app import app, db
from models import (User, Crime, Criminal, CriminalCrime, Case, CaseNote, 
                   Victim, Witness, Evidence, PoliceStation, PoliceOfficer)
from forms import (EditProfileForm, ChangePasswordForm,
                  CrimeForm, CrimeSearchForm, CriminalForm, CriminalSearchForm,
                  CaseForm, CaseNoteForm, CaseSearchForm, VictimForm, WitnessForm,
                  EvidenceForm, PoliceStationForm, PoliceOfficerForm)
from utils import role_required
from replit_auth import require_login, make_replit_blueprint

# Register Replit auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Home and authentication routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html', title='Sign In')

@app.route('/logout')
def logout():
    return redirect(url_for('replit_auth.logout'))

# User management routes
@app.route('/users')
@require_login
@role_required('admin')
def user_list():
    users = User.query.all()
    return render_template('user/list.html', title='User Management', users=users)

@app.route('/users/<string:id>')
@require_login
def user_profile(id):
    user = User.query.get_or_404(id)
    if current_user.id != user.id and not current_user.is_admin():
        abort(403)
    
    return render_template('user/profile.html', title='User Profile', user=user)

@app.route('/users/<string:id>/edit', methods=['GET', 'POST'])
@require_login
def edit_profile(id):
    user = User.query.get_or_404(id)
    if current_user.id != user.id and not current_user.is_admin():
        abort(403)
    
    form = EditProfileForm(user.username, user.email)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_profile', id=user.id))
    
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
    
    return render_template('user/add.html', title='Edit Profile', form=form)

@app.route('/change_role/<string:id>/<string:role>', methods=['POST'])
@require_login
@role_required('admin')
def change_role(id, role):
    if role not in ['admin', 'officer', 'analyst']:
        flash('Invalid role', 'danger')
        return redirect(url_for('user_list'))
    
    user = User.query.get_or_404(id)
    user.role = role
    db.session.commit()
    flash(f'User role updated to {role}', 'success')
    return redirect(url_for('user_list'))

# Dashboard and analytics
@app.route('/dashboard')
@require_login
def dashboard():
    # Get crime statistics for the dashboard
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    start_of_year = date(today.year, 1, 1)
    
    total_crimes = Crime.query.count()
    active_cases = Case.query.filter(Case.status != 'closed').count()
    crimes_this_month = Crime.query.filter(Crime.date >= start_of_month).count()
    crimes_this_year = Crime.query.filter(Crime.date >= start_of_year).count()
    
    # Recent crimes
    recent_crimes = Crime.query.order_by(Crime.date.desc()).limit(5).all()
    
    # Crime types distribution
    crime_types = db.session.query(
        Crime.type, func.count(Crime.id).label('count')
    ).group_by(Crime.type).order_by(desc('count')).limit(5).all()
    
    # Monthly crime trend
    current_year = today.year
    monthly_crimes = db.session.query(
        extract('month', Crime.date).label('month'),
        func.count(Crime.id).label('count')
    ).filter(extract('year', Crime.date) == current_year).group_by('month').all()
    
    # Format data for charts
    months = []
    counts = []
    for i in range(1, 13):
        month_name = calendar.month_abbr[i]
        months.append(month_name)
        
        # Find the count for this month
        count = 0
        for m in monthly_crimes:
            if int(m.month) == i:
                count = m.count
                break
        
        counts.append(count)
    
    # Crime type labels and data for pie chart
    type_labels = [t.type for t in crime_types]
    type_data = [t.count for t in crime_types]
    
    # Get high-priority cases
    high_priority_cases = Case.query.filter_by(priority='high').order_by(Case.updated_at.desc()).limit(3).all()
    
    return render_template('dashboard.html', 
                           title='Dashboard',
                           total_crimes=total_crimes,
                           active_cases=active_cases,
                           crimes_this_month=crimes_this_month,
                           crimes_this_year=crimes_this_year,
                           recent_crimes=recent_crimes,
                           high_priority_cases=high_priority_cases,
                           months=months,
                           counts=counts,
                           type_labels=type_labels,
                           type_data=type_data)

# Crime routes
@app.route('/crimes')
@require_login
def crime_list():
    form = CrimeSearchForm()
    
    page = request.args.get('page', 1, type=int)
    query = Crime.query
    
    # Apply filters if provided
    if request.args.get('search_term'):
        search = "%{}%".format(request.args.get('search_term'))
        query = query.filter(or_(
            Crime.type.like(search),
            Crime.description.like(search),
            Crime.location.like(search)
        ))
    
    if request.args.get('crime_type'):
        query = query.filter(Crime.type == request.args.get('crime_type'))
    
    if request.args.get('date_from'):
        try:
            date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d').date()
            query = query.filter(Crime.date >= date_from)
        except (ValueError, TypeError):
            pass
    
    if request.args.get('date_to'):
        try:
            date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d').date()
            query = query.filter(Crime.date <= date_to)
        except (ValueError, TypeError):
            pass
    
    if request.args.get('location'):
        location = "%{}%".format(request.args.get('location'))
        query = query.filter(Crime.location.like(location))
    
    if request.args.get('status') and request.args.get('status') != '':
        query = query.filter(Crime.status == request.args.get('status'))
    
    # Get unique crime types for filter dropdown
    crime_types = db.session.query(Crime.type).distinct().all()
    crime_types = [t[0] for t in crime_types]
    
    crimes = query.order_by(Crime.date.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('crime/list.html', 
                           title='Crime Records',
                           crimes=crimes,
                           form=form,
                           crime_types=crime_types)

@app.route('/crimes/add', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def add_crime():
    form = CrimeForm()
    
    if form.validate_on_submit():
        crime = Crime()
        crime.type = form.type.data
        crime.description = form.description.data
        crime.date = form.date.data
        crime.time = form.time.data
        crime.location = form.location.data
        crime.latitude = form.latitude.data
        crime.longitude = form.longitude.data
        crime.status = form.status.data
        
        db.session.add(crime)
        db.session.commit()
        flash('Crime record added successfully!', 'success')
        return redirect(url_for('crime_list'))
    
    return render_template('crime/add.html', title='Add Crime Record', form=form)

@app.route('/crimes/<int:id>')
@require_login
def view_crime(id):
    crime = Crime.query.get_or_404(id)
    
    # Get related criminals, victims, witnesses, cases, and evidence
    criminals = db.session.query(Criminal).join(CriminalCrime).filter(CriminalCrime.crime_id == id).all()
    victims = Victim.query.filter_by(crime_id=id).all()
    witnesses = Witness.query.filter_by(crime_id=id).all()
    cases = Case.query.filter_by(crime_id=id).all()
    evidence = Evidence.query.filter_by(crime_id=id).all()
    
    return render_template('crime/view.html',
                          title=f'Crime #{id}',
                          crime=crime,
                          criminals=criminals,
                          victims=victims,
                          witnesses=witnesses,
                          cases=cases,
                          evidence=evidence)

@app.route('/crimes/<int:id>/edit', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def edit_crime(id):
    crime = Crime.query.get_or_404(id)
    form = CrimeForm()
    
    if form.validate_on_submit():
        crime.type = form.type.data
        crime.description = form.description.data
        crime.date = form.date.data
        crime.time = form.time.data
        crime.location = form.location.data
        crime.latitude = form.latitude.data
        crime.longitude = form.longitude.data
        crime.status = form.status.data
        
        db.session.commit()
        flash('Crime record updated successfully!', 'success')
        return redirect(url_for('view_crime', id=crime.id))
    
    elif request.method == 'GET':
        form.type.data = crime.type
        form.description.data = crime.description
        form.date.data = crime.date
        form.time.data = crime.time
        form.location.data = crime.location
        form.latitude.data = crime.latitude
        form.longitude.data = crime.longitude
        form.status.data = crime.status
    
    return render_template('crime/add.html', title='Edit Crime Record', form=form)

# Criminal routes
@app.route('/criminals')
@require_login
def criminal_list():
    form = CriminalSearchForm()
    
    page = request.args.get('page', 1, type=int)
    query = Criminal.query
    
    # Apply filters if provided
    if request.args.get('search_term'):
        search = "%{}%".format(request.args.get('search_term'))
        query = query.filter(or_(
            Criminal.name.like(search),
            Criminal.alias.like(search),
            Criminal.address.like(search),
            Criminal.nationality.like(search)
        ))
    
    if request.args.get('gender') and request.args.get('gender') != '':
        query = query.filter(Criminal.gender == request.args.get('gender'))
    
    if request.args.get('nationality'):
        nationality = "%{}%".format(request.args.get('nationality'))
        query = query.filter(Criminal.nationality.like(nationality))
    
    criminals = query.order_by(Criminal.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('criminal/list.html',
                          title='Criminal Records',
                          criminals=criminals,
                          form=form)

@app.route('/criminals/add', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def add_criminal():
    form = CriminalForm()
    
    if form.validate_on_submit():
        criminal = Criminal()
        criminal.name = form.name.data
        criminal.alias = form.alias.data
        criminal.gender = form.gender.data
        criminal.date_of_birth = form.date_of_birth.data
        criminal.address = form.address.data
        criminal.nationality = form.nationality.data
        criminal.identification_marks = form.identification_marks.data
        criminal.photo_url = form.photo_url.data
        
        db.session.add(criminal)
        db.session.commit()
        flash('Criminal record added successfully!', 'success')
        return redirect(url_for('criminal_list'))
    
    return render_template('criminal/add.html', title='Add Criminal Record', form=form)

@app.route('/criminals/<int:id>')
@require_login
def view_criminal(id):
    criminal = Criminal.query.get_or_404(id)
    
    # Get related crimes
    crimes = db.session.query(Crime).join(CriminalCrime).filter(CriminalCrime.criminal_id == id).all()
    
    return render_template('criminal/view.html',
                          title=f'Criminal - {criminal.name}',
                          criminal=criminal,
                          crimes=crimes)

@app.route('/criminals/<int:id>/edit', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def edit_criminal(id):
    criminal = Criminal.query.get_or_404(id)
    form = CriminalForm()
    
    if form.validate_on_submit():
        criminal.name = form.name.data
        criminal.alias = form.alias.data
        criminal.gender = form.gender.data
        criminal.date_of_birth = form.date_of_birth.data
        criminal.address = form.address.data
        criminal.nationality = form.nationality.data
        criminal.identification_marks = form.identification_marks.data
        criminal.photo_url = form.photo_url.data
        
        db.session.commit()
        flash('Criminal record updated successfully!', 'success')
        return redirect(url_for('view_criminal', id=criminal.id))
    
    elif request.method == 'GET':
        form.name.data = criminal.name
        form.alias.data = criminal.alias
        form.gender.data = criminal.gender
        form.date_of_birth.data = criminal.date_of_birth
        form.address.data = criminal.address
        form.nationality.data = criminal.nationality
        form.identification_marks.data = criminal.identification_marks
        form.photo_url.data = criminal.photo_url
    
    return render_template('criminal/add.html', title='Edit Criminal Record', form=form)

@app.route('/criminals/<int:criminal_id>/add_crime/<int:crime_id>', methods=['POST'])
@require_login
@role_required('officer')
def link_criminal_to_crime(criminal_id, crime_id):
    criminal = Criminal.query.get_or_404(criminal_id)
    crime = Crime.query.get_or_404(crime_id)
    
    # Check if the link already exists
    existing_link = CriminalCrime.query.filter_by(
        criminal_id=criminal_id, crime_id=crime_id).first()
    if existing_link:
        flash('This criminal is already linked to this crime.', 'warning')
        return redirect(url_for('view_crime', id=crime_id))
    
    # Create a new link
    link = CriminalCrime()
    link.criminal_id = criminal_id
    link.crime_id = crime_id
    link.role = request.form.get('role', 'suspect')
    
    db.session.add(link)
    db.session.commit()
    
    flash('Criminal linked to crime successfully!', 'success')
    return redirect(url_for('view_crime', id=crime_id))

# Case routes
@app.route('/cases')
@require_login
def case_list():
    form = CaseSearchForm()
    
    page = request.args.get('page', 1, type=int)
    query = Case.query
    
    # Apply filters if provided
    if request.args.get('search_term'):
        search = "%{}%".format(request.args.get('search_term'))
        query = query.filter(or_(
            Case.title.like(search),
            Case.description.like(search)
        ))
    
    if request.args.get('status') and request.args.get('status') != '':
        query = query.filter(Case.status == request.args.get('status'))
    
    if request.args.get('priority') and request.args.get('priority') != '':
        query = query.filter(Case.priority == request.args.get('priority'))
    
    if request.args.get('officer_id') and request.args.get('officer_id') != '':
        try:
            officer_id = int(request.args.get('officer_id'))
            if officer_id > 0:  # Skip the "All Officers" option
                query = query.filter(Case.officer_id == officer_id)
        except (ValueError, TypeError):
            pass
    
    # Get all officers for the filter dropdown
    officers = User.query.filter(User.role.in_(['admin', 'officer'])).all()
    
    # Prepare the choices for the officer selection dropdown
    form.officer_id.choices = [(0, 'All Officers')] + [(o.id, f"{o.first_name or ''} {o.last_name or ''} ({o.username})") for o in officers]
    
    cases = query.order_by(Case.updated_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('case/list.html',
                          title='Case Management',
                          cases=cases,
                          form=form)

@app.route('/cases/add', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def add_case():
    form = CaseForm()
    
    # Populate the crime and officer selection dropdowns
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"#{c.id}: {c.type} - {c.location}") for c in crimes]
    
    officers = User.query.filter(User.role.in_(['admin', 'officer'])).all()
    form.officer_id.choices = [(o.id, f"{o.first_name or ''} {o.last_name or ''} ({o.username})") for o in officers]
    
    if form.validate_on_submit():
        case = Case()
        case.title = form.title.data
        case.description = form.description.data
        case.status = form.status.data
        case.priority = form.priority.data
        case.crime_id = form.crime_id.data
        case.officer_id = form.officer_id.data
        
        db.session.add(case)
        db.session.commit()
        flash('Case created successfully!', 'success')
        return redirect(url_for('case_list'))
    
    return render_template('case/add.html', title='Create Case', form=form)

@app.route('/cases/<int:id>')
@require_login
def view_case(id):
    case = Case.query.get_or_404(id)
    
    # Get case notes
    notes = CaseNote.query.filter_by(case_id=id).order_by(CaseNote.created_at.desc()).all()
    
    # Create a form for adding new notes
    note_form = CaseNoteForm()
    
    return render_template('case/view.html',
                          title=f'Case: {case.title}',
                          case=case,
                          notes=notes,
                          note_form=note_form)

@app.route('/cases/<int:id>/edit', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def edit_case(id):
    case = Case.query.get_or_404(id)
    
    # Check if the current user is authorized to edit this case
    if not current_user.is_admin() and current_user.id != case.officer_id:
        flash('You are not authorized to edit this case.', 'danger')
        return redirect(url_for('view_case', id=case.id))
    
    form = CaseForm()
    
    # Populate the crime and officer selection dropdowns
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"#{c.id}: {c.type} - {c.location}") for c in crimes]
    
    officers = User.query.filter(User.role.in_(['admin', 'officer'])).all()
    form.officer_id.choices = [(o.id, f"{o.first_name or ''} {o.last_name or ''} ({o.username})") for o in officers]
    
    if form.validate_on_submit():
        case.title = form.title.data
        case.description = form.description.data
        case.status = form.status.data
        case.priority = form.priority.data
        case.crime_id = form.crime_id.data
        case.officer_id = form.officer_id.data
        
        db.session.commit()
        flash('Case updated successfully!', 'success')
        return redirect(url_for('view_case', id=case.id))
    
    elif request.method == 'GET':
        form.title.data = case.title
        form.description.data = case.description
        form.status.data = case.status
        form.priority.data = case.priority
        form.crime_id.data = case.crime_id
        form.officer_id.data = case.officer_id
    
    return render_template('case/add.html', title='Edit Case', form=form)

@app.route('/cases/<int:id>/add_note', methods=['POST'])
@require_login
def add_case_note(id):
    case = Case.query.get_or_404(id)
    form = CaseNoteForm()
    
    if form.validate_on_submit():
        note = CaseNote()
        note.case_id = id
        note.user_id = current_user.id
        note.content = form.content.data
        
        db.session.add(note)
        db.session.commit()
        flash('Note added successfully!', 'success')
    
    return redirect(url_for('view_case', id=id))

# Victim routes
@app.route('/victims')
@require_login
def victim_list():
    page = request.args.get('page', 1, type=int)
    victims = Victim.query.order_by(Victim.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('victim/list.html',
                          title='Victim Records',
                          victims=victims)

@app.route('/victims/add', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def add_victim():
    form = VictimForm()
    
    # Populate the crime selection dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"#{c.id}: {c.type} - {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        victim = Victim()
        victim.name = form.name.data
        victim.gender = form.gender.data
        victim.age = form.age.data
        victim.contact = form.contact.data
        victim.address = form.address.data
        victim.statement = form.statement.data
        victim.crime_id = form.crime_id.data
        
        db.session.add(victim)
        db.session.commit()
        flash('Victim record added successfully!', 'success')
        return redirect(url_for('victim_list'))
    
    return render_template('victim/add.html', title='Add Victim Record', form=form)

@app.route('/victims/<int:id>')
@require_login
def view_victim(id):
    victim = Victim.query.get_or_404(id)
    return render_template('victim/view.html',
                          title=f'Victim: {victim.name}',
                          victim=victim)

@app.route('/victims/<int:id>/edit', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def edit_victim(id):
    victim = Victim.query.get_or_404(id)
    form = VictimForm()
    
    # Populate the crime selection dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"#{c.id}: {c.type} - {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        victim.name = form.name.data
        victim.gender = form.gender.data
        victim.age = form.age.data
        victim.contact = form.contact.data
        victim.address = form.address.data
        victim.statement = form.statement.data
        victim.crime_id = form.crime_id.data
        
        db.session.commit()
        flash('Victim record updated successfully!', 'success')
        return redirect(url_for('view_victim', id=victim.id))
    
    elif request.method == 'GET':
        form.name.data = victim.name
        form.gender.data = victim.gender
        form.age.data = victim.age
        form.contact.data = victim.contact
        form.address.data = victim.address
        form.statement.data = victim.statement
        form.crime_id.data = victim.crime_id
    
    return render_template('victim/add.html', title='Edit Victim Record', form=form)

# Witness routes
@app.route('/witnesses')
@require_login
def witness_list():
    page = request.args.get('page', 1, type=int)
    witnesses = Witness.query.order_by(Witness.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('witness/list.html',
                          title='Witness Records',
                          witnesses=witnesses)

@app.route('/witnesses/add', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def add_witness():
    form = WitnessForm()
    
    # Populate the crime selection dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"#{c.id}: {c.type} - {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        witness = Witness()
        witness.name = form.name.data
        witness.contact = form.contact.data
        witness.address = form.address.data
        witness.statement = form.statement.data
        witness.relation_to_victim = form.relation_to_victim.data
        witness.crime_id = form.crime_id.data
        
        db.session.add(witness)
        db.session.commit()
        flash('Witness record added successfully!', 'success')
        return redirect(url_for('witness_list'))
    
    return render_template('witness/add.html', title='Add Witness Record', form=form)

@app.route('/witnesses/<int:id>')
@require_login
def view_witness(id):
    witness = Witness.query.get_or_404(id)
    return render_template('witness/view.html',
                          title=f'Witness: {witness.name}',
                          witness=witness)

@app.route('/witnesses/<int:id>/edit', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def edit_witness(id):
    witness = Witness.query.get_or_404(id)
    form = WitnessForm()
    
    # Populate the crime selection dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"#{c.id}: {c.type} - {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        witness.name = form.name.data
        witness.contact = form.contact.data
        witness.address = form.address.data
        witness.statement = form.statement.data
        witness.relation_to_victim = form.relation_to_victim.data
        witness.crime_id = form.crime_id.data
        
        db.session.commit()
        flash('Witness record updated successfully!', 'success')
        return redirect(url_for('view_witness', id=witness.id))
    
    elif request.method == 'GET':
        form.name.data = witness.name
        form.contact.data = witness.contact
        form.address.data = witness.address
        form.statement.data = witness.statement
        form.relation_to_victim.data = witness.relation_to_victim
        form.crime_id.data = witness.crime_id
    
    return render_template('witness/add.html', title='Edit Witness Record', form=form)

# Evidence routes
@app.route('/evidence')
@require_login
def evidence_list():
    page = request.args.get('page', 1, type=int)
    evidence_list = Evidence.query.order_by(Evidence.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('evidence/list.html',
                          title='Evidence Records',
                          evidence_list=evidence_list)

@app.route('/evidence/add', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def add_evidence():
    form = EvidenceForm()
    
    # Populate the crime selection dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"#{c.id}: {c.type} - {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        evidence = Evidence()
        evidence.name = form.name.data
        evidence.type = form.type.data
        evidence.description = form.description.data
        evidence.location_found = form.location_found.data
        evidence.collection_date = form.collection_date.data
        evidence.custodian = form.custodian.data
        evidence.storage_location = form.storage_location.data
        evidence.crime_id = form.crime_id.data
        
        db.session.add(evidence)
        db.session.commit()
        flash('Evidence record added successfully!', 'success')
        return redirect(url_for('evidence_list'))
    
    return render_template('evidence/add.html', title='Add Evidence Record', form=form)

@app.route('/evidence/<int:id>')
@require_login
def view_evidence(id):
    evidence = Evidence.query.get_or_404(id)
    return render_template('evidence/view.html',
                          title=f'Evidence: {evidence.name}',
                          evidence=evidence)

@app.route('/evidence/<int:id>/edit', methods=['GET', 'POST'])
@require_login
@role_required('officer')
def edit_evidence(id):
    evidence = Evidence.query.get_or_404(id)
    form = EvidenceForm()
    
    # Populate the crime selection dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"#{c.id}: {c.type} - {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        evidence.name = form.name.data
        evidence.type = form.type.data
        evidence.description = form.description.data
        evidence.location_found = form.location_found.data
        evidence.collection_date = form.collection_date.data
        evidence.custodian = form.custodian.data
        evidence.storage_location = form.storage_location.data
        evidence.crime_id = form.crime_id.data
        
        db.session.commit()
        flash('Evidence record updated successfully!', 'success')
        return redirect(url_for('view_evidence', id=evidence.id))
    
    elif request.method == 'GET':
        form.name.data = evidence.name
        form.type.data = evidence.type
        form.description.data = evidence.description
        form.location_found.data = evidence.location_found
        form.collection_date.data = evidence.collection_date
        form.custodian.data = evidence.custodian
        form.storage_location.data = evidence.storage_location
        form.crime_id.data = evidence.crime_id
    
    return render_template('evidence/add.html', title='Edit Evidence Record', form=form)

# Police Station routes
@app.route('/stations')
@require_login
def station_list():
    page = request.args.get('page', 1, type=int)
    stations = PoliceStation.query.order_by(PoliceStation.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('station/list.html',
                          title='Police Stations',
                          stations=stations)

@app.route('/stations/add', methods=['GET', 'POST'])
@require_login
@role_required('admin')
def add_station():
    form = PoliceStationForm()
    
    if form.validate_on_submit():
        station = PoliceStation()
        station.name = form.name.data
        station.address = form.address.data
        station.contact = form.contact.data
        station.latitude = form.latitude.data
        station.longitude = form.longitude.data
        
        db.session.add(station)
        db.session.commit()
        flash('Police station added successfully!', 'success')
        return redirect(url_for('station_list'))
    
    return render_template('station/add.html', title='Add Police Station', form=form)

@app.route('/stations/<int:id>')
@require_login
def view_station(id):
    station = PoliceStation.query.get_or_404(id)
    officers = PoliceOfficer.query.filter_by(station_id=id).all()
    
    return render_template('station/view.html',
                          title=f'Police Station: {station.name}',
                          station=station,
                          officers=officers)

@app.route('/stations/<int:id>/edit', methods=['GET', 'POST'])
@require_login
@role_required('admin')
def edit_station(id):
    station = PoliceStation.query.get_or_404(id)
    form = PoliceStationForm()
    
    if form.validate_on_submit():
        station.name = form.name.data
        station.address = form.address.data
        station.contact = form.contact.data
        station.latitude = form.latitude.data
        station.longitude = form.longitude.data
        
        db.session.commit()
        flash('Police station updated successfully!', 'success')
        return redirect(url_for('view_station', id=station.id))
    
    elif request.method == 'GET':
        form.name.data = station.name
        form.address.data = station.address
        form.contact.data = station.contact
        form.latitude.data = station.latitude
        form.longitude.data = station.longitude
    
    return render_template('station/add.html', title='Edit Police Station', form=form)

# Police Officer routes
@app.route('/officers')
@require_login
def officer_list():
    page = request.args.get('page', 1, type=int)
    officers = PoliceOfficer.query.order_by(PoliceOfficer.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('officer/list.html',
                          title='Police Officers',
                          officers=officers)

@app.route('/officers/add', methods=['GET', 'POST'])
@require_login
@role_required('admin')
def add_officer():
    form = PoliceOfficerForm()
    
    # Populate the station selection dropdown
    stations = PoliceStation.query.all()
    form.station_id.choices = [(s.id, s.name) for s in stations]
    
    # Populate the user account selection dropdown
    # Only include users who don't already have an officer profile
    existing_officer_users = db.session.query(PoliceOfficer.user_id).filter(PoliceOfficer.user_id != None)
    users = User.query.filter(User.id.notin_(existing_officer_users)).all()
    
    # Add a None option for officers without user accounts
    form.user_id.choices = [(0, 'None')] + [(u.id, f"{u.first_name or ''} {u.last_name or ''} ({u.username})") for u in users]
    
    if form.validate_on_submit():
        officer = PoliceOfficer()
        officer.name = form.name.data
        officer.rank = form.rank.data
        officer.badge_number = form.badge_number.data
        officer.contact = form.contact.data
        officer.station_id = form.station_id.data
        
        # Only set user_id if a user was selected (not the 'None' option)
        if form.user_id.data != 0:
            officer.user_id = form.user_id.data
        
        db.session.add(officer)
        db.session.commit()
        flash('Police officer added successfully!', 'success')
        return redirect(url_for('officer_list'))
    
    return render_template('officer/add.html', title='Add Police Officer', form=form)

@app.route('/officers/<int:id>')
@require_login
def view_officer(id):
    officer = PoliceOfficer.query.get_or_404(id)
    return render_template('officer/view.html',
                          title=f'Police Officer: {officer.name}',
                          officer=officer)

@app.route('/officers/<int:id>/edit', methods=['GET', 'POST'])
@require_login
@role_required('admin')
def edit_officer(id):
    officer = PoliceOfficer.query.get_or_404(id)
    form = PoliceOfficerForm()
    
    # Populate the station selection dropdown
    stations = PoliceStation.query.all()
    form.station_id.choices = [(s.id, s.name) for s in stations]
    
    # Populate the user account selection dropdown
    # Include the currently assigned user (if any) and users who don't have an officer profile
    existing_officer_users = db.session.query(PoliceOfficer.user_id).filter(
        PoliceOfficer.user_id != None, PoliceOfficer.id != id)
    users = User.query.filter(User.id.notin_(existing_officer_users)).all()
    
    # Add a None option for officers without user accounts
    form.user_id.choices = [(0, 'None')] + [(u.id, f"{u.first_name or ''} {u.last_name or ''} ({u.username})") for u in users]
    
    if form.validate_on_submit():
        officer.name = form.name.data
        officer.rank = form.rank.data
        officer.badge_number = form.badge_number.data
        officer.contact = form.contact.data
        officer.station_id = form.station_id.data
        
        # Only set user_id if a user was selected (not the 'None' option)
        if form.user_id.data != 0:
            officer.user_id = form.user_id.data
        else:
            officer.user_id = None
        
        db.session.commit()
        flash('Police officer updated successfully!', 'success')
        return redirect(url_for('view_officer', id=officer.id))
    
    elif request.method == 'GET':
        form.name.data = officer.name
        form.rank.data = officer.rank
        form.badge_number.data = officer.badge_number
        form.contact.data = officer.contact
        form.station_id.data = officer.station_id
        form.user_id.data = officer.user_id if officer.user_id else 0
    
    return render_template('officer/add.html', title='Edit Police Officer', form=form)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Map view
@app.route('/map')
@require_login
def crime_map():
    # Get crimes with coordinates
    crimes = Crime.query.filter(Crime.latitude != None, Crime.longitude != None).all()
    
    # Get police stations with coordinates
    stations = PoliceStation.query.filter(PoliceStation.latitude != None, PoliceStation.longitude != None).all()
    
    return render_template('map.html', title='Crime Map', crimes=crimes, stations=stations)

# Analytics
@app.route('/analytics')
@require_login
@role_required('analyst')
def analytics():
    # Time period for analysis
    period = request.args.get('period', 'year')
    
    today = date.today()
    if period == 'month':
        start_date = date(today.year, today.month, 1)
        title_period = f"{calendar.month_name[today.month]} {today.year}"
    elif period == 'quarter':
        current_quarter = (today.month - 1) // 3 + 1
        start_month = (current_quarter - 1) * 3 + 1
        start_date = date(today.year, start_month, 1)
        title_period = f"Q{current_quarter} {today.year}"
    else:  # year
        start_date = date(today.year, 1, 1)
        title_period = str(today.year)
    
    # Crime type distribution
    crime_types = db.session.query(
        Crime.type, func.count(Crime.id).label('count')
    ).filter(Crime.date >= start_date).group_by(Crime.type).order_by(desc('count')).all()
    
    # Crime status distribution
    crime_statuses = db.session.query(
        Crime.status, func.count(Crime.id).label('count')
    ).filter(Crime.date >= start_date).group_by(Crime.status).all()
    
    # Crime trend over time (daily for month, monthly for year/quarter)
    if period == 'month':
        # Daily trend for the current month
        crime_trend = db.session.query(
            func.date(Crime.date).label('date'),
            func.count(Crime.id).label('count')
        ).filter(Crime.date >= start_date).group_by('date').all()
        
        # Format data for charts - daily
        days = []
        daily_counts = []
        
        # Get all days in the month
        num_days = calendar.monthrange(today.year, today.month)[1]
        for day in range(1, num_days + 1):
            current_date = date(today.year, today.month, day)
            if current_date <= today:
                days.append(day)
                
                # Find the count for this day
                count = 0
                for trend in crime_trend:
                    if trend.date.day == day:
                        count = trend.count
                        break
                
                daily_counts.append(count)
        
        trend_labels = days
        trend_data = daily_counts
        trend_label = "Daily Crimes"
    else:
        # Monthly trend for quarter/year
        crime_trend = db.session.query(
            extract('month', Crime.date).label('month'),
            func.count(Crime.id).label('count')
        ).filter(Crime.date >= start_date).group_by('month').all()
        
        # Format data for charts - monthly
        months = []
        monthly_counts = []
        
        # Get all months in the period
        start_month = start_date.month
        end_month = today.month
        for month_num in range(start_month, end_month + 1):
            month_name = calendar.month_abbr[month_num]
            months.append(month_name)
            
            # Find the count for this month
            count = 0
            for trend in crime_trend:
                if int(trend.month) == month_num:
                    count = trend.count
                    break
            
            monthly_counts.append(count)
        
        trend_labels = months
        trend_data = monthly_counts
        trend_label = "Monthly Crimes"
    
    # Format data for charts
    type_labels = [t.type for t in crime_types]
    type_data = [t.count for t in crime_types]
    
    status_labels = [s.status.capitalize() for s in crime_statuses]
    status_data = [s.count for s in crime_statuses]
    
    # Get total count
    total_crimes = sum([t.count for t in crime_types])
    
    return render_template('analytics.html',
                          title=f'Crime Analytics - {title_period}',
                          period=period,
                          total_crimes=total_crimes,
                          type_labels=type_labels,
                          type_data=type_data,
                          status_labels=status_labels,
                          status_data=status_data,
                          trend_labels=trend_labels,
                          trend_data=trend_data,
                          trend_label=trend_label)

# API routes for charts
@app.route('/api/crime_stats')
@require_login
def api_crime_stats():
    # Time period filter
    period = request.args.get('period', 'year')
    
    today = date.today()
    if period == 'month':
        start_date = date(today.year, today.month, 1)
    elif period == 'quarter':
        current_quarter = (today.month - 1) // 3 + 1
        start_month = (current_quarter - 1) * 3 + 1
        start_date = date(today.year, start_month, 1)
    else:  # year
        start_date = date(today.year, 1, 1)
    
    # Get crime stats
    crime_types = db.session.query(
        Crime.type, func.count(Crime.id).label('count')
    ).filter(Crime.date >= start_date).group_by(Crime.type).order_by(desc('count')).all()
    
    # Format data for JSON response
    data = {
        'labels': [t.type for t in crime_types],
        'datasets': [{
            'data': [t.count for t in crime_types],
            'backgroundColor': [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', 
                '#FF9F40', '#8BC34A', '#607D8B', '#E91E63', '#03A9F4'
            ]
        }]
    }
    
    return jsonify(data)

@app.route('/api/crime_trend')
@require_login
def api_crime_trend():
    # Time period filter
    period = request.args.get('period', 'year')
    
    today = date.today()
    if period == 'month':
        start_date = date(today.year, today.month, 1)
        # Daily trend for the current month
        crime_trend = db.session.query(
            func.date(Crime.date).label('date'),
            func.count(Crime.id).label('count')
        ).filter(Crime.date >= start_date).group_by('date').all()
        
        # Format data for charts - daily
        days = []
        daily_counts = []
        
        # Get all days in the month
        num_days = calendar.monthrange(today.year, today.month)[1]
        for day in range(1, num_days + 1):
            current_date = date(today.year, today.month, day)
            if current_date <= today:
                days.append(str(day))
                
                # Find the count for this day
                count = 0
                for trend in crime_trend:
                    if trend.date.day == day:
                        count = trend.count
                        break
                
                daily_counts.append(count)
        
        labels = days
        data = daily_counts
    else:
        if period == 'quarter':
            current_quarter = (today.month - 1) // 3 + 1
            start_month = (current_quarter - 1) * 3 + 1
            start_date = date(today.year, start_month, 1)
        else:  # year
            start_date = date(today.year, 1, 1)
        
        # Monthly trend for quarter/year
        crime_trend = db.session.query(
            extract('month', Crime.date).label('month'),
            func.count(Crime.id).label('count')
        ).filter(Crime.date >= start_date).group_by('month').all()
        
        # Format data for charts - monthly
        months = []
        monthly_counts = []
        
        # Get all months in the period
        start_month = start_date.month
        end_month = today.month
        for month_num in range(start_month, end_month + 1):
            month_name = calendar.month_abbr[month_num]
            months.append(month_name)
            
            # Find the count for this month
            count = 0
            for trend in crime_trend:
                if int(trend.month) == month_num:
                    count = trend.count
                    break
            
            monthly_counts.append(count)
        
        labels = months
        data = monthly_counts
    
    # Format data for JSON response
    response = {
        'labels': labels,
        'datasets': [{
            'label': 'Crime Count',
            'data': data,
            'borderColor': '#36A2EB',
            'backgroundColor': 'rgba(54, 162, 235, 0.2)',
            'tension': 0.1
        }]
    }
    
    return jsonify(response)

# Data export routes
@app.route('/export/crimes')
@require_login
@role_required('analyst')
def export_crimes():
    # Export crime data as CSV
    # Implementation will depend on how you want to handle file downloads
    # For now, we'll just redirect to the crimes list
    flash('Data export feature is not implemented yet.', 'warning')
    return redirect(url_for('crime_list'))