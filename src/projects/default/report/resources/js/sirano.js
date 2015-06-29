var siranoApp = angular.module('siranoApp', ['smart-table']);

siranoApp.controller('siranoCtrl', function ($scope, $http, $filter) {

    $scope.report = jsondata;
    $scope.errors = 0;
    $scope.warnings = 0;
    $scope.infos = 0;
    $scope.success = 0;

    $scope.getTotal = function (values, key) {
        sum = 0;
        angular.forEach(values, function (v, k) {
            if (v.hasOwnProperty(key)) {
                sum += v[key];
            }
        });
        return sum;
    };

    $scope.getUniqueId = function () {
        $scope.getUniqueId.id = $scope.getUniqueId.id + 1 || 0;
        return $scope.getUniqueId.id
    };

    $('a[href]').attr({'target': '_self'});

    $scope.incrementCounters = function (success, infos, warnings, errors) {
        $scope.warnings += warnings;
        $scope.errors += errors;
        $scope.infos += infos;
        $scope.success += success


        $scope.updateDonutSuccess()
    };

    $scope.donut_success = Morris.Donut({
        element: 'donut-success',
        colors: ['#5CB85C',
            '#337AB7',
            '#F0AD4E',
            '#D9534F'
        ],
        formatter: function (y, data) {
            return y + '%'
        },
        data: [
            {label: "Success", value: 0},
            {label: "Infos", value: 0},
            {label: "Warnings", value: 0},
            {label: "Errors", value: 0}
        ]
    });

    $scope.updateDonutSuccess = function () {
        total = 1 * $scope.success + 0.1 * $scope.infos + 100 * $scope.warnings;
        success = Math.round($scope.success / total * 100);
        infos = Math.round(0.1 * $scope.infos / total * 100);
        warnings = Math.round(100 * $scope.warnings / total * 100);

        if ($scope.errors) {
            errors = 100;
            success = 0;
            infos = 0;
            warings = 0;

            $scope.donut_success.setData([
                {label: 'Anonymization failed', value: 0},
                {label: 'Anonymization failed', value: 0},
                {label: 'Anonymization failed', value: 0},
                {label: "Anonymization failed", value: errors}
            ]);
        } else {

            $scope.donut_success.setData([
                {label: "Success", value: success},
                {label: "Infos", value: infos},
                {label: "Warnings", value: warnings}
            ]);
        }
    }
});