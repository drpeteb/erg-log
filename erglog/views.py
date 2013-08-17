from pyramid.response import Response
from pyramid.httpexceptions import(
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.view import view_config
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )
from pyramid.renderers import render

from sqlalchemy.exc import DBAPIError

from .models import (
    DBI,
    DBSession,
    Rower,
    ErgTypeDistance,
    ErgTypeTime,
    ErgRecordDistance,
    ErgRecordTime,
    )

from .security import get_password

from .erg_time_handling import *

import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates
import StringIO
#import xkcdify

@view_config(route_name='login', renderer='templates/generic_page.pt')
def login(request):
    
    message = 'Please log in.'

    if 'form.login_submitted' in request.params:
        username = request.params['username']
        password = request.params['password']
        if get_password(username) == password:
            headers = remember(request, username)
            return HTTPFound(location=request.route_url('home'),
                             headers=headers)
        message = 'Login failed. Try again.'

    body = render('templates/login.pt', dict(), request)
    return dict(message=message, body=body)



@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location = request.route_url('login'), headers = headers)



@view_config(route_name='home', renderer='templates/generic_page.pt', permission='standard')
def home(request):
    
    username = authenticated_userid(request)
    rower = DBI.get_rower_by_username(username)
    
    erg_type_distance_list = DBI.list_all(ErgTypeDistance)
    erg_type_time_list = DBI.list_all(ErgTypeTime)
    
    if 'form.distance_erg_record_added' in request.params:
        # Adding an erg record
        still_good = True
        distance = int(request.params['distance_erg_distance'])

        try:
            time_min = int(request.params['distance_erg_time_min'])
            time_sec = int(request.params['distance_erg_time_sec'])
            time_ten = int(request.params['distance_erg_time_ten'])
            time = input_time(time_min, time_sec, time_ten)
        except ValueError:
            message = 'Please use numbers to record your time.'
            still_good = False

        try:
            date = dt.datetime.strptime(request.params['distance_erg_date'], '%Y-%m-%d')
        except ValueError:
            message = 'I don\'t recognise that date.'
            still_good = False
        
        if still_good:
            erg_record = ErgRecordDistance(rower.id, date, time, distance)
            try:
                DBI.add_to_db(erg_record)
                message='Added new distance erg: '+ rower.name + ' rowed ' + str(distance) + 'm in ' + output_time(time) + ' minutes on ' + str(date.date()) + '. Thankyou.'
            except DBAPIError:
                message='Failed to add new erg. You\'ve probably already recorded one for that date. Sorry.'

#    elif 'form.display_requested' in request.params:
#        # Table or graph requested
#        rower_id = request.params['rower_id']
#        display_type = request.params['display_type']
#        return HTTPFound(location = request.route_url(display_type,rower_id=rower_id))

    else:
        # Otherwise return default
        message='Welcome to ErgLog, %s. Enjoy your stay.' % rower.name

    temp_dict = dict(erg_type_distance_list=erg_type_distance_list,
                     erg_type_time_list=erg_type_time_list,)
    body = render('templates/home.pt', temp_dict, request)
    return dict(message=message, body=body)


@view_config(route_name='admin', renderer='templates/generic_page.pt', permission='admin')
def admin_page(request):

    rower_list = DBI.list_all(Rower)

    if 'form.rower_added' in request.params:
        # Adding a rower
        rower_username = request.params['username']
        rower_password = request.params['password']
        rower_name = request.params['rower_name']
        rower = Rower(rower_username, rower_password, rower_name)
        try:
            DBI.add_to_db(rower)
            message='Added new rower: ' + rower_name + '. Thankyou.'
        except DBAPIError:
            message='Failed to add new rower. The username or name probably already exists. Sorry.'

    elif 'form.distance_erg_added' in request.params:
        # Adding a new distance erg
        try:
            erg_distance = int(request.params['distance'])
            if erg_distance < 0:
                message = 'Ya can\'t row a negative distance.'
            elif erg_distance > 20000:
                message = str(erg_distance) + 'm! That\'s too far.'
            else:
                erg_type = ErgTypeDistance(erg_distance)
                DBI.add_to_db(erg_type)
                message='Added a new distance erg type: ' + str(erg_distance) + 'm. Thankyou.'
        except ValueError:
            message = 'I don\'t understand that distance.'
        except DBAPIError:
            message = 'I think that distance already exists.'
            
    elif 'form.time_erg_added' in request.params:
        # Adding a new time erg
        try:
            erg_time = int(request.params['time'])
            if erg_time < 0:
                message = 'Ya can\'t row for a negative time.'
            elif erg_time > 120:
                message = str(erg_time) + 'min! That\'s too long.'
            else:
                erg_type = ErgTypeTime(erg_time)
                DBI.add_to_db(erg_type)
                message='Added a new time erg type: ' + str(erg_time) + 'min. Thankyou.'
        except ValueError:
            message = 'I don\'t understand that time.'
        except DBAPIError:
            message = 'I think that time already exists.'

    else:
        # Otherwise return default
        message='Welcome master. What is your command?'

    body = render('templates/admin.pt', dict(rower_list=rower_list), request)
    return dict(message=message, body=body)









@view_config(route_name='table', renderer='templates/table.pt')
def erg_table(request):
    # Make a list of ergs to display
    rower_id = int(request.matchdict['rower_id'])
    if rower_id == 0:
        erg_list = DBSession.query(ErgRecord).all()
    else:
        erg_list = DBSession.query(ErgRecord).filter_by(rower_id=rower_id).all()

    # If there aren't any, 404 it
    if not erg_list:
        return HTTPNotFound('No such page')
        
    # Sort and convert to text
    entries = []
    erg_list.sort(key=lambda erg: erg.date)
    for erg in erg_list:
        date = datetime.datetime.strftime(erg.date,'%Y-%m-%d')
        rower = DBSession.query(Rower).filter_by(id=erg.rower_id).one().name
        distance = str(erg.distance)
        split = str(erg.split)
        entry = {"date":date, "rower":rower, "distance":distance, "split":split}
        entries.append(entry)

    return {"entries":entries}


@view_config(route_name='graph', renderer='templates/graph.pt')
def erg_graph(request):
    # Make a list of ergs to display
    rower_id = int(request.matchdict['rower_id'])
    if rower_id == 0:
        erg_list = DBSession.query(ErgRecord).all()
    else:
        erg_list = DBSession.query(ErgRecord).filter_by(rower_id=rower_id).all()
    erg_list.sort(key=lambda erg: erg.date)
    
    # Strip out dates and distances
    dates = []
    distances = []
    for erg in erg_list:
        dates.append(erg.date)
        distances.append(erg.distance)

    # Create a plot
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot_date(dates, distances, '-')
    fig.autofmt_xdate()
    
    # Output a string
    virtual_file = StringIO.StringIO()
    fig.savefig(virtual_file, format='svg')
    virtual_file.seek(0)
    svg_data = virtual_file.buf
    start_point = svg_data.find('<svg')
    svg_data = svg_data[start_point:]

    return {"svg_data":svg_data}

