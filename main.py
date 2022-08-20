from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("Flask_Secret_ket")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top10-movie-data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)

db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(500))
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


class RateMovieForm(FlaskForm):
    new_rating = StringField('Your rating out of 10 e.g. 7.5',
                             validators=[InputRequired(message="This field cannot be left empty")])
    new_review = StringField('Updated Review',
                             validators=[InputRequired(message="This field cannot be left empty")])
    done = SubmitField('Done')


class AddNewMovieForm(FlaskForm):
    movie_title = StringField('Movie Title', validators=[InputRequired(message="This field cannot be left empty")])
    add_movie = SubmitField('Add Movie')


API_KEY = os.environ.get("Movie_Database_API")


@app.route("/")
def home():
    # This line creates a list of all the movies sorted by rating in ascending order
    all_movies = Movie.query.order_by(Movie.rating).all()

    # This line creates a "list" of all the movies sorted by rating in descending order
    # all_movies = Movie.query.order_by(desc(Movie.rating)).all()

    #This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        # i.e., ranking started backwards
        all_movies[i].ranking = len(all_movies) - i

        # This line gives each movie a new ranking acc. to their order in "all_movies list"
        # all_movies[i].ranking = i + 1
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    if request.method == "POST" and form.validate_on_submit():
        movie_to_update = Movie.query.get(movie_id)
        movie_to_update.rating = float(form.new_rating.data)
        movie_to_update.review = form.new_review.data
        db.session.commit()
        return redirect(url_for('home'))
    movie = Movie.query.get(movie_id)
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete", methods=["GET", "POST"])
def delete_movie():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add_movie", methods=["GET", "POST"])
def add_movie():
    form = AddNewMovieForm()
    if form.validate_on_submit():
        movie_title = form.movie_title.data
        return redirect(url_for("select_movie", searched_movie=movie_title))
    return render_template("add.html", form=form)


@app.route("/select_movie")
def select_movie():
    movie_parameters = {
        "api_key": API_KEY,
        "language": "en-US",
        "query": request.args.get('searched_movie')
    }
    url = "https://api.themoviedb.org/3/search/movie"

    response = requests.get(url, params=movie_parameters)
    all_matched_movies = response.json()["results"]
    return render_template("select.html", all_searched_movies=all_matched_movies)


@app.route("/add_movie_in_database")
def add_movie_in_database():
    movie_parameters = {
        "api_key": API_KEY,
    }
    url = f"https://api.themoviedb.org/3/movie/{request.args.get('id')}"

    response = requests.get(url, params=movie_parameters)

    title = response.json()["original_title"]
    img_url = f"https://image.tmdb.org/t/p/original/{response.json()['poster_path']}"
    year = response.json()["release_date"].split("-")[0]
    description = response.json()["overview"]

    new_movie = Movie(title=title, year=year, description=description,
                      img_url=img_url)
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
