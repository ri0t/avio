import icon from './assets/avio_menu_logo.svg';

export function routing($stateProvider) {

    $stateProvider
        .state('app.avio', {
            url: '/avio',
            template: '<avio></avio>',
            label: 'AVIO',
            icon: icon
        });
}
