/**
 * Copyright ©2018. The Regents of the University of California (Regents). All Rights Reserved.
 *
 * Permission to use, copy, modify, and distribute this software and its documentation
 * for educational, research, and not-for-profit purposes, without fee and without a
 * signed licensing agreement, is hereby granted, provided that the above copyright
 * notice, this paragraph and the following two paragraphs appear in all copies,
 * modifications, and distributions.
 *
 * Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
 * Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
 * http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.
 *
 * IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
 * INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
 * THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
 * SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
 * "AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
 * ENHANCEMENTS, OR MODIFICATIONS.
 */

(function(angular) {

  'use strict';

  angular.module('boac').directive('curatedCohortSelector', function(
    authService,
    studentGroupFactory,
    studentGroupService,
    $rootScope,
    $timeout
  ) {

    return {
      // @see https://docs.angularjs.org/guide/directive#template-expanding-directive
      restrict: 'E',

      // @see https://docs.angularjs.org/guide/directive#isolating-the-scope-of-a-directive
      scope: {
        students: '='
      },

      templateUrl: '/static/app/group/groupsSelector.html',

      link: function(scope) {

        scope.isLoading = true;

        scope.selector = {
          selectAllCheckbox: false,
          showCuratedCohortMenu: false
        };

        /**
         * Show or hide the student-groups menu based on page state.
         *
         * @return {void}
         */
        var updateCuratedCohortMenu = function() {
          scope.selector.showCuratedCohortMenu = scope.selector.selectAllCheckbox || !!_.find(scope.students, 'selectedForCuratedCohort');
        };

        var initStudent = function(student) {
          // Init all student checkboxes to false
          student.selectedForCuratedCohort = false;
          student.curatedCohortToggle = function(event) {
            event.stopPropagation();
            if (student.selectedForCuratedCohort) {
              var allStudentsSelected = true;
              _.each(scope.students, function(_student) {
                if (!_student.selectedForCuratedCohort) {
                  // We found a checkbox not checked. The 'all' checkbox must be false.
                  allStudentsSelected = false;
                  // Break out of loop.
                  return false;
                }
              });
              scope.selector.selectAllCheckbox = allStudentsSelected;
            } else {
              scope.selector.selectAllCheckbox = false;
            }
            updateCuratedCohortMenu();
          };
        };

        var init = function() {
          var me = authService.getMe();
          scope.myGroups = me.myGroups;
          _.each(scope.students, initStudent);
          scope.isLoading = false;
        };

        init();

        /**
         * Toggle the all-student-groups checkbox.
         *
         * @param  {Boolean}    value      If true, select all students in current page view.
         * @return {void}
         */
        var toggleAllStudentCheckboxes = scope.toggleAllStudentCheckboxes = function(value) {
          var selected = _.isNil(value) ? scope.selector.selectAllCheckbox : value;
          _.each(scope.students, function(student) {
            student.selectedForCuratedCohort = selected;
          });
          scope.selector.selectAllCheckbox = selected;
          updateCuratedCohortMenu();
          scope.selector.showCuratedCohortMenu = selected;
        };

        /**
         * Add selected students to the group provided and then reset all student-group related menus.
         *
         * @param  {Group}    group      Students will be added to this group.
         * @return {void}
         */
        var groupCheckboxClick = scope.groupCheckboxClick = function(group) {
          scope.isSaving = true;
          var students = _.filter(scope.students, function(student) {
            return student.selectedForCuratedCohort && !studentGroupService.isStudentInGroup(student, group);
          });
          if (students.length) {
            studentGroupFactory.addStudentsToGroup(group, students).then(function() {
              scope.selector.selectAllCheckbox = false;
              _.each(scope.students, function(student) {
                student.selectedForCuratedCohort = false;
              });
            });
          }
          _.each(scope.myGroups, function(g) {
            if (g) {
              g.selected = false;
            }
          });
          scope.selector.selectAllCheckbox = false;
          $timeout(function() {
            toggleAllStudentCheckboxes(false);
            scope.isSaving = false;
          }, 2000);
        };


        $rootScope.$on('groupCreated', function(event, data) {
          var group = data.group;
          scope.myGroups.push(group);
          groupCheckboxClick(group);
        });

        $rootScope.$on('resetCuratedCohortSelector', function() {
          toggleAllStudentCheckboxes(false);
        });
      }
    };
  });

}(window.angular));