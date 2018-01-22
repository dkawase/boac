(function(angular) {

  'use strict';

  angular.module('boac').controller('LandingController', function(authService, cohortFactory, watchlistFactory, $rootScope, $scope) {

    $scope.isLoading = true;
    $scope.isAuthenticated = authService.isAuthenticatedUser();

    var init = function() {
      if ($scope.isAuthenticated) {
        cohortFactory.getTeams().then(function(teamsResponse) {
          $scope.teams = teamsResponse.data;

          cohortFactory.getMyCohorts().then(function(cohortsResponse) {
            $scope.myCohorts = cohortsResponse.data;

            watchlistFactory.getMyWatchlist().then(function(response) {
              $scope.myWatchlist = response.data;
              $scope.isLoading = false;
            });
          });
        });
      } else {
        $scope.isLoading = false;
      }
    };

    $rootScope.$on('devAuthFailure', function() {
      $scope.alertMessage = 'Log in failed. Please try again.';
    });

    $rootScope.$on('watchlistRemoval', function(event, sidRemoved) {
      $scope.myWatchlist = _.reject($scope.myWatchlist, ['sid', sidRemoved]);
    });

    init();
  });

}(window.angular));
