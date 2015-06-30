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
        $scope.success += success;
        $scope.updateDonutUsability()
    };

    $scope.donut_usability = Morris.Donut({
        element: 'donut-usability',
        colors: ['#5CB85C',
            '#337AB7',
            '#F0AD4E',
            '#D9534F'
        ],
        formatter: function (y, data) {
            return data.data + '%'
        },
        data: [
            {label: "Success", value: 0},
            {label: "Infos", value: 0},
            {label: "Warnings", value: 0},
            {label: "Errors", value: 0}
        ]
    });

    $scope.updateDonutUsability = function () {
        total = $scope.success + $scope.infos + $scope.warnings;
        success = Math.round($scope.success / total * 100);
        infos = Math.round($scope.infos / total * 100);
        warnings = Math.round($scope.warnings / total * 100);

        if ($scope.errors) {
            $scope.donut_usability.setData([
                {label: 'Anonymization failed', value: 0},
                {label: 'Anonymization failed', value: 0},
                {label: 'Anonymization failed', value: 0},
                {label: "Anonymization failed", value: 100}
            ]);
        } else {
            $scope.donut_usability.setData([
                {label: "Usability", value: success, data: success},
                {label: "Usability", value: infos, data: success},
                {label: "Usability", value: warnings, data: success}
            ]);
        }
    }
});