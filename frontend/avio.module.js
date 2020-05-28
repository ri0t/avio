import angular from 'angular';
import uirouter from 'angular-ui-router';

import {routing} from './avio.config.js';

import './avio/avio.scss';

import aviocomponent from './avio/avio.js';
import template from './avio/avio.tpl.html';

export default angular
    .module('main.app.avio', [uirouter])
    .config(routing)
    .component('avio', {controller: aviocomponent, template: template})
    .name;
