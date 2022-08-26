from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import requests

API_KEY = 'YOUR_API_KEY' #https://api.themoviedb.org

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SOME_SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)

db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True)
    year = db.Column(db.String(250))
    description = db.Column(db.String(250))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(250))

    # Optional: this will allow each movie object to be identified by its title when printed.
    def __repr__(self):
        return '<Movie %r>' % self.title

class MovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])

    submit = SubmitField("Done")

class AddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])

    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()
    return render_template("index.html", movies = movies)

@app.route("/edit", methods=['GET', 'POST'])
def edit():
    movie_id = request.args.get("movie_id")
    form = MovieForm()
    movie = Movie.query.get(movie_id)
    if request.method == 'POST' and form.validate():
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template("edit.html", movie = movie, form=form)

@app.route("/delete")
def delete():
    movie_id = request.args.get("movie_id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

def get_movie_info(title):
    params = {'api_key':API_KEY,
              'query':title}
    response = requests.get(url='https://api.themoviedb.org/3/search/movie', params=params)
    result = response.json()['results']
    return params, result

@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddForm()
    if request.method == 'POST' and form.validate():
        params, movies_to_select = get_movie_info(form.title.data)

        return render_template('select.html', movies=movies_to_select, api_key=API_KEY)
    else:
        return render_template('add.html', form=form)

@app.route("/find", methods=['GET', 'POST'])
def find_movie():
    IMG_BASE_PATH = 'https://image.tmdb.org/t/p/original'
    movie_id = request.args.get("movie_id")
    response = requests.get(url=f'https://api.themoviedb.org/3/movie/{movie_id}', params={'api_key':API_KEY})
    result = response.json()
    img_url = IMG_BASE_PATH+result['poster_path']
    title = result['title']
    year = result['release_date'][:4]
    description = result['overview']
    new_movie = Movie(title=title,year=year, description=description, img_url=img_url)
    db.session.add(new_movie)
    db.session.commit()
    movie_id = Movie.query.filter_by(title=title).first().id
    return redirect(url_for('edit', movie_id = movie_id))


if __name__ == '__main__':
    app.run(debug=True)
