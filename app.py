#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
# from flask_sqlalchemy import SQLAlchemy
from models import db, Show, Artist, Venue
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
# from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  venues_map = Venue.query.all()
  venue_set = set()
  for venue in venues_map:
    venue_set.add((venue.city, venue.state))
  
  for i in venue_set:
      city_state = {
          "city": i[0],
          "state": i[1]
      }
      venues = Venue.query.filter_by(city=i[0], state=i[1]).all()
      venue_format = []
      for venue in venues:
          venue_format.append({
              "id": venue.id,
              "name": venue.name,
              "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
          })
      
      city_state["venues"] = venue_format
      data.append(city_state)
  
  return render_template('pages/venues.html', areas=data)

#search venues
@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = request.form.get("search_term")
  response = (Venue.query.filter((
    Venue.city.ilike('%' + search + '%') |
    Venue.name.ilike('%' + search + '%') |
    Venue.state.ilike('%' + search + '%'))
    ))
  return render_template('pages/search_venues.html', results=response, search=request.form.get('search_term', ' '))


#show venue
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = Venue.query.get(venue_id)

  upcoming_shows = Show.query.join(Venue).filter(Venue.id == venue_id).filter(Show.start_time > datetime.utcnow())
  all_future_shows = []
  for show in upcoming_shows:
      con_future = {}
      con_future["artist_name"] = show.artists.name
      con_future["artist_id"] = show.artists.id
      con_future["artist_image_link"] = show.artists.image_link
      con_future["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
      all_future_shows.append(con_future)

  setattr(data, "upcoming_shows", all_future_shows)    
  setattr(data,"upcoming_shows_count", upcoming_shows.count())

  past_shows = Show.query.join(Venue).filter(Venue.id == venue_id).filter(Show.start_time <= datetime.utcnow())
  all_past_shows = []
  for show in past_shows:
        con_past = {}
        con_past["artist_name"] = show.artists.name
        con_past["artist_id"] = show.artists.id
        con_past["artist_image_link"] = show.artists.image_link
        con_past["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        all_past_shows.append(con_past)

  setattr(data, "past_shows", all_past_shows)
  setattr(data,"past_shows_count", past_shows.count())

  return render_template('pages/show_venue.html', venue=data)
  

  

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  if form.validate():
      add = request.form.get  
      try:
        new_venue = Venue(name=add('name'),
                          city=add('city'),
                          state=add('state'),
                          address=add('address'),
                          phone=add('phone'),
                          genres=request.form.getlist('genres'),
                          website=add('website_link'),
                          facebook_link=add('facebook_link'),
                          seeking_talent=form.seeking_talent.data,
                          seeking_description=add('seeking_description')
                          )
        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
      except Exception as e:
          print(e)
          db.session.rollback()
          flash('An error occurred. Venue ' + add('name') + ' could not be listed.')
      finally:
        db.session.close()
  else:
      print(form.errors)
      flash('An error occurred with the form. Check form and try again')
  return redirect(url_for('index'))

 

@app.route('/venues/delete/<venue_id>')
def delete_venue(venue_id):
  try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
      flash("Venue " + venue.name + " was deleted successfully!")
  except:
      db.session.rollback()
      flash("Venue was not deleted successfully.")
  finally:
      db.session.close()
  return redirect(url_for("index"))


#edit venue
#----------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.genres.data = venue.genres
  form.state.data = venue.state
  form.city.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link
  form.website_link.data = venue.website
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  return render_template('forms/edit_venue.html', form=form, venue=venue)



@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  if form.validate():
      try:
          venue = Venue.query.get(venue_id)
          venue.name = form.name.data
          venue.city=form.city.data
          venue.state=form.state.data
          venue.address=form.address.data
          venue.phone=form.phone.data
          venue.genres=form.genres.data 
          venue.facebook_link=form.facebook_link.data
          venue.image_link=form.image_link.data
          venue.seeking_talent=form.seeking_talent.data
          venue.seeking_description=form.seeking_description.data
          venue.website=form.website_link.data

          db.session.add(venue)
          db.session.commit()
          flash("Venue " + venue.name + " was successfully edited!")
      except:
          db.session.rollback()
          flash("Venue " + venue.name + " was not successfully edited!")
      finally:
          db.session.close()
  else:
      print(form.errors)
      flash("An Occured while editing. Check form and try again")
  return redirect(url_for('show_venue', venue_id=venue_id))
 

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = db.session.query(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=artists)
 

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = request.form.get("search_term")
  response = (Artist.query.filter(
    (Artist.city.ilike('%' + search + '%') |
    Artist.name.ilike('%' + search + '%') |
    Artist.state.ilike('%' + search + '%'))
    ))
  return render_template('pages/search_artists.html', results=response, search=request.form.get('search_term', ' '))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = Artist.query.get(artist_id)
  upcoming_shows = Show.query.join(Artist).filter(Artist.id == artist_id).filter(Show.start_time > datetime.utcnow())
  all_future_shows = []
  for show in upcoming_shows:
      con_future = {}
      con_future["venue_name"] = show.venues.name
      con_future["venue_id"] = show.venue.id
      con_future["venue_image_link"] = show.venues.image_link
      con_future["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
      all_future_shows.append(con_future)

  setattr(data, "upcoming_shows", all_future_shows)    
  setattr(data,"upcoming_shows_count", upcoming_shows.count())

  past_shows = Show.query.join(Artist).filter(Artist.id == artist_id).filter(Show.start_time <= datetime.utcnow())
  all_past_shows = []
  for show in past_shows:
        con_past = {}
        con_past["venue_name"] = show.venues.name
        con_past["venue_id"] = show.venues.id
        con_past["venue_image_link"] = show.venues.image_link
        con_past["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        all_past_shows.append(con_past)

  setattr(data, "past_shows", all_past_shows)
  setattr(data,"past_shows_count", past_shows.count())
  
  return render_template('pages/show_artist.html', artist=data)
  
#delete artist
@app.route('/artists/delete/<artist_id>')
def delete_artist(artist_id):
  try:
      artist = Artist.query.get(artist_id)
      db.session.delete(artist)
      db.session.commit()
      flash("artist " + artist.name + " was deleted successfully!")
  except:
      db.session.rollback()
      flash("artist was not deleted successfully.")
  finally:
      db.session.close()
  return redirect(url_for("index"))

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.genres.data = artist.genres
  form.state.data = artist.state
  form.city.data = artist.state
  form.phone.data = artist.phone
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  form.website_link.data = artist.website
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  return render_template('forms/edit_artist.html', form=form, artist=artist)


 
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)

  if form.validate():
      try:
          artist = Artist.query.get(artist_id)
          artist.name = form.name.data
          artist.city=form.city.data
          artist.state=form.state.data
          artist.phone=form.phone.data
          artist.genres=form.genres.data 
          artist.facebook_link=form.facebook_link.data
          artist.image_link=form.image_link.data
          artist.seeking_venue=form.seeking_venue.data
          artist.seeking_description=form.seeking_description.data
          artist.website=form.website_link.data

          db.session.add(artist)
          db.session.commit()
          flash("Artist " + artist.name + " was successfully edited!")
      except:
          db.session.rollback()
          flash("Artist " + artist.name + " was not successfully edited!")
      finally:
          db.session.close()
  else:
      print(form.errors)
      flash("An Occured while editing. Check form and try again")

  return redirect(url_for('show_artist', artist_id=artist_id))
  

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  if form.validate():
      add = request.form.get  
      # try:
      new_artist = Artist(name=add('name'),
                        city=add('city'),
                        state=add('state'),
                        phone=add('phone'),
                        genres=request.form.getlist('genres'),
                        website=add('website_link'),
                        facebook_link=add('facebook_link'),
                        seeking_venue=form.seeking_venue.data,
                        seeking_description=add('seeking_description')
                        )
      db.session.add(new_artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
      # except:
      #     db.session.rollback()
      #     flash('An error occurred. Artist ' + ' ' + add('name') + ' could not be listed.')
      # finally:
      #   db.session.close()
  else:
      print(form.errors)
      flash('An error occurred with the form. Check form and try again')
  return redirect(url_for('index'))

  


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  data = []

  for show in shows:
      show_unit = {}
      show_unit["venue_id"] = show.venues.id
      show_unit["venue_name"] = show.venues.name
      show_unit["artist_id"] = show.artists.id
      show_unit["artist_name"] = show.artists.name
      show_unit["artist_image_link"] = show.artists.image_link
      show_unit["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    
      data.append(show_unit)
    
  return render_template('pages/shows.html', shows=data)
 

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  if form.validate():
        try:
          artist_id = request.form.get('artist_id')
          venue_id = request.form.get('venue_id')
          artist = Artist.query.get(artist_id)
          venue = Venue.query.get(venue_id)
          show = Show(artist_id=artist.id,
                      venue_id=venue.id,
                      start_time=request.form.get('start_time')
                    )
          db.session.add(show)
          db.session.commit()
          flash('Show was successfully listed!')
        except:
          db.session.rollback()
          flash('Show could not be listed successfully!')
        finally:
          db.session.close()           
  else:
      print(form.errors)
      flash('An error occurred.  check the form and try again')
  return redirect(url_for('index'))
 


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
if __name__ == '__main__':
    # port = int(os.environ.get('PORT', 5000))
    
    app.run(debug=True, host='0.0.0.0', port=5000)

