"""
Copyright ©2019. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""

from boac import db, std_commit
from boac.models.base import Base
from sqlalchemy.dialects.postgresql import ARRAY


class Note(Base):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, nullable=False, primary_key=True)  # noqa: A003
    author_uid = db.Column(db.String(255), nullable=False)
    author_name = db.Column(db.String(255), nullable=False)
    author_role = db.Column(db.String(255), nullable=False)
    author_dept_codes = db.Column(ARRAY(db.String), nullable=False)
    sid = db.Column(db.String(80), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)

    def __init__(self, author_uid, author_name, author_role, author_dept_codes, sid, subject, body):
        self.author_uid = author_uid
        self.author_name = author_name
        self.author_role = author_role
        self.author_dept_codes = author_dept_codes
        self.sid = sid
        self.subject = subject
        self.body = body

    @classmethod
    def find_by_id(cls, note_id):
        return cls.query.filter_by(id=note_id).first()

    @classmethod
    def create(cls, author_uid, author_name, author_role, author_dept_codes, sid, subject, body):
        note = cls(author_uid, author_name, author_role, author_dept_codes, sid, subject, body)
        db.session.add(note)
        std_commit()
        return note

    @classmethod
    def update(cls, note_id, subject, body):
        note = cls.find_by_id(note_id=note_id)
        if note:
            note.subject = subject
            note.body = body
            std_commit()
            return note
        else:
            return None

    @classmethod
    def get_notes_by_sid(cls, sid):
        return cls.query.filter(cls.sid == sid).all()

    def to_api_json(self):
        return {
            'id': self.id,
            'authorUid': self.author_uid,
            'authorName': self.author_name,
            'authorRole': self.author_role,
            'authorDeptCodes': self.author_dept_codes,
            'sid': self.sid,
            'subject': self.subject,
            'body': self.body,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at,
        }
