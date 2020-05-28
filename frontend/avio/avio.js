'use strict';

class aviocomponent {

    constructor(scope, socket, $state, $rootScope, user, schemata) {
        this.scope = scope;
        this.socket = socket;
        this.state = $state;
        this.rootscope = $rootScope;
        this.user = user;
        this.schemata = schemata;

        let self = this;

        self.mixer_model = {};
        self.mixer_schema = {};
        self.mixer_form = {};


        this.output = [];
        this.player_frames = {
            A: [],
            B: []
        }
        this.control_data = "";

        for (let i=0; i <16; i++) {
            let col = [];
            for (let j=0; j <40; j++) {
                col.push([255, 0, 0]);
            }
            this.output.push(col);
            this.player_frames.A.push(col);
            this.player_frames.B.push(col);
        }

        this.axes = {};
        this.buttons = {};

        this.mixer = {
            0: {
                alpha: 0.5
            },
            1: {
                alpha: 0.75
            },
            2: {
                alpa: 0
            }
        }
        this.players = {}

        console.log('[AVIO] Initializing');

        this.toggle_player = function(player) {
            console.log('Toggling player:', player)
            this.players[player].playing = !this.players[player].playing;
            this.update_player(player);
        }

        this.stop_player = function(player) {
            console.log('Stopping Player:', player)
            if (this.players[player].playing)
                this.toggle_player(player);
        }
        this.remove_player = function(player) {
            console.log('Removing Player:', player)
            let request = {
                component: 'avio.gifplayer',
                action: 'remove_player',
                data: player
            }
            this.socket.send(request)
        }

        this.add_video = function(video, slot_number) {
            console.log('[AVIO] Adding video:', video, slot_number);
            let request = {
                component: 'avio.gifplayer',
                action: 'add_player',
                data: {
                    channel: slot_number,
                    filename: video
                }
            }
            this.socket.send(request);
        }


        this.forward = function(player) {
            console.log('Forward Player:', player)
        }

        this.backward = function(player) {
            console.log('Backward Player:', player)
        }

        this.step_forward = function(player) {
            console.log('Step Forward Player:', player)
        }

        this.step_backward = function(player) {
            console.log('Step Backward Player:', player)
        }

        this.fast_forward = function(player) {
            console.log('Fast Forward Player:', player)
        }

        this.fast_backward = function(player) {
            console.log('Fast Backward Player:', player)
        }


        this.ml_subscribe = function() {
            this.subscribe('isomer.matelightsim');
        }


        this.ml_unsubscribe = function() {
            this.unsubscribe('isomer.matelightsim');
        }

        this.ctl_subscribe = function() {
            this.subscribe('avio.controller');
        }


        this.ctl_unsubscribe = function() {
            this.unsubscribe('avio.controller');
        }

        this.video_subscribe = function() {
            this.subscribe('avio.gifplayer')
        }

        this.library_subscribe = function() {
            this.subscribe('avio.library')
        }

        this.library_open = function() {
            if (!this.library) {
                this.library_subscribe();
            }
        }
        this.subscribe = function(part) {
            console.log('[AVIO] Subscribing', part);

            self.socket.send({
                component: part,
                action: 'subscribe',
            });
        };
        this.unsubscribe = function(part) {
            console.log('[AVIO] Unsubscribing', part);

            self.socket.send({
                component: part,
                action: 'unsubscribe',
            });
        };

        this.unsubscribe_all = function() {
            self.unsubscribe('isomer.matelightsim');
            self.unsubscribe('avio.controller');
            self.unsubscribe('avio.gifplayer');
            self.unsubscribe('avio.library');
        }

        this.ml_update = function(msg) {
            self.output = msg.data;
        }

        this.video_update = function(msg) {
            if (msg.action === 'frame_update') {
                self.player_frames[msg.data.channel] = msg.data.frame
            } else if (msg.action === 'get_data') {
                console.log('[AVIO] GIFMASTER:', msg.data)
            } else if (msg.action === 'add_player') {
                console.log('[AVIO] Added player:', msg.data);
                self.players[msg.data.channel] = msg.data;
            } else if (msg.action === 'change_player') {
                console.log('[AVIO] Changed Player');
                self.players[msg.data.channel] = msg.data;
            } else if (msg.action === 'remove_player') {
                console.log('[AVIO] Removed Player', msg.data, self.players);
                delete self.players[msg.data];
            }
        }

        this.update_player = function(player) {
            let request = {
                component: 'avio.gifplayer',
                action: 'change_player',
                data: this.players[player]
            }

            this.socket.send(request);
        }

        this.switch_singleshot = function(player) {
            this.players[player].bounce = false;
            this.players[player].loop = false;

            this.update_player(player);
        }
        this.switch_reverse = function(player) {
            this.players[player].reverse = !this.players[player].reverse;

            this.update_player(player);
        }
        this.switch_bounce = function(player) {
            this.players[player].bounce = !this.players[player].bounce;
            if (this.players[player].bounce === true) {
                this.players[player].loop = false;
            }

            this.update_player(player);
        }
        this.switch_loop = function(player) {
            this.players[player].loop = !this.players[player].loop;
            if (this.players[player].loop === true) {
                this.players[player].bounce = false;
            }

            this.update_player(player);
        }

        this.library_update = function(msg) {
            if (msg.action === 'library') {
                self.library = msg.data;
            }
        }

        this.ctl_update = function(msg) {
            console.log(msg);
            if (msg.data.hasOwnProperty('axis')) {
                self.axes[msg.data.axis] = msg.data.value;
                self.axis_data = msg.data
            } else if (msg.data.hasOwnProperty('button')) {
                self.buttons[msg.data.button] = msg.data.action == "JoyButtonDown"
                self.control_data = msg.data
            }
            //<Event(7-JoyAxisMotion {'joy': 0, 'axis': 4, 'value': 0.2989593188268685})>
        }

        this.mix_update = function(msg) {
            console.log('[AVIO] Mixer Update:', msg);
            self.mixer_model = msg.data;
        }

        this.getData = function () {
            console.log('[AVIO] Getting config ');
            self.schemata.updateconfigschemata();
            let request = {
                component: 'avio.videomixer',
                action: 'get_data'
            }
            self.socket.send(request);
        }

        if (this.user.signedin) {
            console.log("[AVIO] Logged in, subscribing")
            this.getData()
        }

        this.matelightupdate = this.socket.listen('isomer.matelightsim', self.ml_update)
        this.controlupdate = this.socket.listen('avio.controller', self.ctl_update)
        this.mixerupdate = this.socket.listen('avio.videomixer', self.mix_update)
        this.videoupdate = this.socket.listen('avio.gifplayer', self.video_update)
        this.libraryupdate = this.socket.listen('avio.library', self.library_update)

        this.loginupdate = this.rootscope.$on('User.Login', self.getData);
        this.schemaupdate = this.rootscope.$on('Schemata.ConfigUpdate', function () {
            console.log('[AVIO] Configuration Schema update.');
            self.configschemadata = self.schemata.configschemata;
            self.configschemata = Object.keys(self.configschemadata);
            self.mixer_schema = self.configschemadata['VideoMixer'].schema
            self.mixer_form = self.configschemadata['VideoMixer'].form
        });

        self.scope.$on('$destroy', function () {
            self.unsubscribe_all();
            self.loginupdate();
            self.schemaupdate();
            
            self.socket.unlisten('isomer.matelightsim');
            self.socket.unlisten('avio.controller');
            self.socket.unlisten('avio.videomixer');
            self.socket.unlisten('avio.gifplayer');
            self.socket.unlisten('avio.library');
        });
    }

    getElementStyle(col) {
        return {background: "rgb(" + col[0] + ", " + col[1] + ", " + col[2] + ")"}
    }

    getDuration(playtime) {
        var date = new Date(null);
        date.setSeconds(playtime);
        return date.toISOString().substr(11, 8);
    }
}

aviocomponent.$inject = ['$scope', 'socket', '$state', '$rootScope', 'user', 'schemata'];

export default aviocomponent;
