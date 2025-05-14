import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from flask_login import UserMixin
from typing import List
from app import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(80), unique=True, nullable=False)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(200), nullable=False)
    
    # Connect
    polls: so.Mapped["Poll"] = so.relationship(back_populates="user")
    answer: so.Mapped["Answer"] = so.relationship(back_populates="user")


class Poll(db.Model):
    __tablename__ = 'polls'
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    
    # Connect
    user: so.Mapped["User"] = so.relationship(back_populates="polls")
    questions: so.Mapped[List["Question"]] = so.relationship(back_populates="poll", uselist=True)
    answer: so.Mapped[List["Answer"]] = so.relationship(back_populates="poll", uselist=True)

class Question(db.Model):
    __tablename__ = 'questions'
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    text: so.Mapped[str] = so.mapped_column(sa.String(500), nullable=False)
    type: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False)  # text, radio, checkbox
    options: so.Mapped[str] = so.mapped_column(sa.String(500), nullable=True)
    poll_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('polls.id'), nullable=False)

    # Connect
    poll: so.Mapped["Poll"] = so.relationship(back_populates="questions")
    answers: so.Mapped["Answer"] = so.relationship(back_populates="question")

class Answer(db.Model):
    __tablename__ = 'answers'
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.String(1000), nullable=False)
    question_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('questions.id'), nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('users.id'))
    poll_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('polls.id'))
    timestamp: so.Mapped[datetime] = so.mapped_column(default=datetime.now(timezone.utc))

    # Connect
    user: so.Mapped["User"] = so.relationship(back_populates="answer")
    poll: so.Mapped["Poll"] = so.relationship(back_populates="answer")
    question: so.Mapped["Question"] = so.relationship(back_populates="answers")