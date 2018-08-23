"""
Copyright ©2018. The Regents of the University of California (Regents). All Rights Reserved.

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


from boac.models.authorized_user import AuthorizedUser
from boac.models.curated_cohort import CuratedCohort
import pytest
import simplejson as json


admin_uid = '2040'
asc_advisor_uid = '6446'
coe_advisor_uid = '1133399'


@pytest.fixture()
def asc_advisor(fake_auth):
    fake_auth.login(asc_advisor_uid)


@pytest.fixture()
def coe_advisor(fake_auth):
    fake_auth.login(coe_advisor_uid)


@pytest.fixture()
def admin_user_session(fake_auth):
    fake_auth.login(admin_uid)


class TestCuratedCohortsController:
    """CuratedCohort API."""

    def test_not_authenticated(self, client):
        """Returns 401 if not authenticated."""
        assert client.get('/api/curated_cohorts/my').status_code == 401

    def test_unauthorized(self, admin_user_session, client):
        """Rejects authenticated user if s/he does not own the curated_cohort."""
        advisor_with_curated_cohort = AuthorizedUser.find_by_uid('6446')
        curated_cohorts = CuratedCohort.get_curated_cohorts_by_owner_id(advisor_with_curated_cohort.id)
        response = client.get(f'/api/curated_cohort/{curated_cohorts[0].id}')
        assert response.status_code == 403

    def test_my_curated_cohorts(self, asc_advisor, client):
        """Returns all of current_user's student curated_cohorts."""
        response = client.get('/api/curated_cohorts/my')
        assert response.status_code == 200
        curated_cohorts = response.json
        assert len(curated_cohorts) == 2
        default_curated_cohort = next(curated_cohort for curated_cohort in curated_cohorts if curated_cohort['name'] == 'My Students')
        assert len(default_curated_cohort['students']) == 0
        cool_kids_curated_cohort = next(curated_cohort for curated_cohort in curated_cohorts if curated_cohort['name'] == 'Cool Kids')
        assert cool_kids_curated_cohort['studentCount'] == 4

    def test_empty_curated_cohort(self, admin_user_session, client):
        """Returns default empty curated_cohort requested."""
        curated_cohorts = client.get('/api/curated_cohorts/my').json
        default_curated_cohort = next(curated_cohort for curated_cohort in curated_cohorts if curated_cohort['name'] == 'My Students')
        response = client.get(f'/api/curated_cohort/{default_curated_cohort["id"]}')
        assert response.status_code == 200
        assert response.json['students'] == []

    def test_curated_cohort_summary_excludes_students_without_alerts(self, asc_advisor, create_alerts, client, db_session):
        """When all curated_cohorts are requested, returns only students with alerts."""
        curated_cohorts = client.get('/api/curated_cohorts/my').json
        assert curated_cohorts[0]['studentCount'] == 4
        assert len(curated_cohorts[0]['students']) == 2
        assert curated_cohorts[0]['students'][0]['alertCount'] == 3
        assert curated_cohorts[0]['students'][1]['alertCount'] == 1

        alert_to_dismiss = client.get('/api/alerts/current/11667051').json['shown'][0]['id']
        client.get('/api/alerts/' + str(alert_to_dismiss) + '/dismiss')
        curated_cohorts = client.get('/api/curated_cohorts/my').json
        assert curated_cohorts[0]['students'][0]['alertCount'] == 2

    def test_curated_cohort_detail_includes_students_without_alerts(self, asc_advisor, create_alerts, client):
        """When curated_cohort detail is requested, returns all students."""
        curated_cohorts = client.get('/api/curated_cohorts/my').json
        curated_cohort = client.get(f'/api/curated_cohort/{curated_cohorts[0]["id"]}').json
        assert curated_cohort['students'][0]['alertCount'] == 3
        assert 'alertCount' not in curated_cohort['students'][1]
        assert 'alertCount' not in curated_cohort['students'][2]
        assert curated_cohort['students'][3]['alertCount'] == 1

    def test_curated_cohort_index_includes_summary(self, asc_advisor, create_alerts, client):
        """Returns summary details but not full term and analytics data for curated_cohort index."""
        curated_cohorts = client.get('/api/curated_cohorts/my').json
        students = curated_cohorts[0]['students']
        assert students[0]['cumulativeGPA'] == 3.8
        assert students[0]['cumulativeUnits'] == 101.3
        assert students[0]['level'] == 'Junior'
        assert len(students[0]['majors']) == 2
        assert 'analytics' not in students[0]
        assert 'enrollments' not in students[0]['term']

    def test_curated_cohort_detail_includes_analytics(self, asc_advisor, client):
        """Returns all students with full term and analytics data for detailed curated_cohort listing."""
        curated_cohorts = client.get('/api/curated_cohorts/my').json
        curated_cohort = next(curated_cohort for curated_cohort in curated_cohorts if curated_cohort['name'] == 'Cool Kids')
        curated_cohort_id = curated_cohort['id']
        curated_cohort = client.get(f'/api/curated_cohort/{curated_cohort_id}').json
        students = curated_cohort['students']
        assert students[0]['cumulativeGPA'] == 3.8
        assert students[0]['cumulativeUnits'] == 101.3
        assert students[0]['level'] == 'Junior'
        assert len(students[0]['majors']) == 2
        assert 'analytics' in students[0]
        assert 'enrollments' in students[0]['term']

    def test_curated_cohort_detail_includes_athletics(self, asc_advisor, client):
        """Returns all students with athletic memberships for detailed curated_cohort listing."""
        curated_cohorts = client.get('/api/curated_cohorts/my').json
        curated_cohort = next(curated_cohort for curated_cohort in curated_cohorts if curated_cohort['name'] == 'Cool Kids')
        curated_cohort_id = curated_cohort['id']
        curated_cohort = client.get(f'/api/curated_cohort/{curated_cohort_id}').json
        students = curated_cohort['students']
        teams = students[0]['athleticsProfile']['athletics']
        assert len(teams) == 2
        assert teams[0]['name'] == 'Women\'s Field Hockey'
        assert teams[0]['groupCode'] == 'WFH'
        assert teams[1]['name'] == 'Women\'s Tennis'
        assert teams[1]['groupCode'] == 'WTE'

    def test_curated_cohort_detail_omits_athletics_non_asc(self, coe_advisor, client):
        curated_cohorts = client.get('/api/curated_cohorts/my').json
        curated_cohort = next(c for c in curated_cohorts if c['name'] == 'Cohort of One')
        curated_cohort_id = curated_cohort['id']
        curated_cohort = client.get(f'/api/curated_cohort/{curated_cohort_id}').json
        assert 'athleticsProfile' not in curated_cohort['students'][0]

    def test_add_multiple_students_to_curated_cohort(self, asc_advisor, client):
        """Create curated cohort and add students."""
        name = 'Cheap Tricks'
        response = client.post(
            '/api/curated_cohort/create',
            data=json.dumps({'name': name}),
            content_type='application/json',
        )
        curated_cohort = json.loads(response.data)

        # Add students and include invalid sid and dupe sids. Expect no "duplicate key violates" error.
        response = client.post(
            '/api/curated_cohort/students/add',
            data=json.dumps({
                'curatedCohortId': curated_cohort['id'],
                'sids': ['2345678901', '11667051', '2345678901', 'ABC'],
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        updated_curated_cohort = json.loads(response.data)
        assert updated_curated_cohort['id'] == curated_cohort['id']
        assert len(updated_curated_cohort['students']) == 2

    def test_create_add_remove_and_delete(self, asc_advisor, client):
        """Create a curated_cohort, add a student, remove the student and then delete the curated_cohort."""
        name = 'Fun Boy Three'
        response = client.post(
            '/api/curated_cohort/create',
            data=json.dumps({'name': name}),
            content_type='application/json',
        )
        curated_cohort = json.loads(response.data)
        curated_cohort_id = curated_cohort['id']

        # Add student
        sid = '2345678901'
        response = client.get(f'/api/curated_cohort/{curated_cohort_id}/add_student/{sid}')
        assert response.status_code == 200
        curated_cohort = client.get(f'/api/curated_cohort/{curated_cohort_id}').json
        assert curated_cohort['name'] == name
        assert curated_cohort['students'][0]['sid'] == sid
        # Remove student
        response = client.delete(f'/api/curated_cohort/{curated_cohort_id}/remove_student/{sid}')
        assert response.status_code == 200
        curated_cohort = client.get(f'/api/curated_cohort/{curated_cohort_id}').json
        assert curated_cohort['name'] == name
        assert not len(curated_cohort['students'])
        # Rename curated_cohort
        new_name = 'Teenage Wasteland'
        response = client.post(
            '/api/curated_cohort/rename',
            data=json.dumps({'id': curated_cohort_id, 'name': new_name}),
            content_type='application/json',
        )
        assert response.status_code == 200
        curated_cohort = client.get(f'/api/curated_cohort/{curated_cohort_id}').json
        assert curated_cohort['name'] == new_name
        # Delete curated_cohort
        response = client.delete(f'/api/curated_cohort/delete/{curated_cohort_id}')
        assert response.status_code == 200
        # Verify
        response = client.get(f'/api/curated_cohort/{curated_cohort_id}')
        assert response.status_code == 404
