'use strict';

function BottomScroller(props) {
    return (
        <h1>{props.txt}</h1>
    );
}

function TopScroller(props) {
    return (
        <h1>{props.txt}</h1>
    )
}

function Notifier(props) {
    return (
        props.txt?<div id="notification">{props.txt}</div>:null
    );
}


class Alerts extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            event: null,
            follows: Array(5),
            subs: Array(5),
            notifymsg : null,
            simconnected: false,
            ias: 0,
            gs: 0,
            vs: 0,
            heading: 0,
            alt: 0,
            oat: 0,
            fuel_quant: 0,
            fuel_cap: 0,
            onground: true
        }
        this.timerId = null;
        this.intervalID = null;
        this.socket = new WebSocket('ws://' + window.location.hostname + ':' + window.location.port +'/ws');
    }
    follow_audio = new Audio('follower_chord.wav');
    raid_audio = new Audio('raid.wav');

    componentDidMount() {
        this.registerWsHandlers();
        this.intervalID = setInterval(
            () => this.tick(),
            1000
          );        
    }

    registerWsHandlers() {
        this.socket.onmessage = (data) => {
            //console.dir(data.data);
            var incoming = JSON.parse(data.data)
            if (incoming.type == "twitch")
                this.handleTwitchEvent(incoming.event)
            else if (incoming.type == "simconnect")
                this.handleSimconnectEvent(incoming.event)
            else {
                console.error("Unknown message type")
                dir(incoming)
            }
        }
    }

    tick() {
        if(this.socket.readyState ===  WebSocket.CLOSED) {
            this.socket = new WebSocket('ws://' + window.location.hostname + ':' + window.location.port +'/ws');
            this.registerWsHandlers();
        }
    }

    handleTwitchEvent(event) {
        if (event.subscription.type == 'channel.follow')
            this.newFollow(event.event.user_name)
        else if (event.subscription.type == 'channel.raid')
            this.raid(event.event.from_broadcaster_user_name, event.event.viewers)
        else if (event.subscription.type == 'channel.subscribe')
            this.subscribe(event.event.user_name, event.event.tier)
        else if (event.subscription.type == 'channel.cheer')
            this.cheer(event.event.user_name, event.event.bits)
        else if (event.subscription.type == 'channel.channel_points_custom_reward_redemption.add')
            this.claimReward(event.event.user_name, event.event.reward.title);
        else if (event.subscription.type == 'channel.subscription.gift') {
            if(event.event.is_anonymous)
                this.cheer("Anonymous", event.event.bits)
            else
                this.cheer(event.event.user_name, event.event.total)
        }
        else {
            console.log(`Unknown twitch event ${event.subscription.type}`)
        }

    }

    handleSimconnectEvent(event) {
        if (event.connected) {
            this.setState({
                simconnected: true,
                ias: event.AIRSPEED_INDICATED,
                gs: event.GROUND_VELOCITY,
                vs: event.VERTICAL_SPEED,
                heading: event.MAGNETIC_COMPASS,
                alt: event.PLANE_ALTITUDE,
                oat: event.AMBIENT_TEMPERATURE,
                fuel_quant: event.FUEL_TOTAL_QUANTITY,
                fuel_cap: event.FUEL_TOTAL_CAPACITY,
                onground: event.SIM_ON_GROUND==1?true:false            
            });
        }
        else {
            this.setState({
                simconnected: false
            })
        }
    }

    componentWillUnmount() {
        this.socket.send('close');
        this.socket.close();
    }

    newFollow(name) {
        var currFollows = this.state.follows
        if (currFollows.includes(name))
            return
        if (currFollows.length >= 5)
            currFollows.shift()
        currFollows.push(name)
        this.setState({
            follows: currFollows
        })
        this.updateNotifyPanel(`Follow from ${name}`);
        this.follow_audio.play();
    }

    updateNotifyPanel(message) {
        this.setState({
            notifymsg: message
        });
        if (this.timerId) {
            clearTimeout(this.timerId);
        }
        this.timerId = setTimeout(()=>{this.resetNotify()}, 5000);
    }

    resetNotify() {
        this.setState({
            notifymsg: null
        });
        this.timerId = null;
    }

    raid(from, viewers) {
        this.updateNotifyPanel(`Raid by ${from} with a party of ${viewers}`)
        this.raid_audio.play();
    }

    cheer(from, bits) {
        this.updateNotifyPanel(`${from} cheered  ${bits} bits`)
        this.follow_audio.play();
    }

    subscribe(from, tier) {
        var currSubs = this.state.subs
        if (currSubs.length >= 5)
            currSubs.shift()
        currSubs.push(from)
        this.setState({
            subs: currSubs
        })
        console.dir(currSubs)
        this.updateNotifyPanel(`${from} subscribed at ${tier} tier`)
        this.follow_audio.play();
    }

    gifted(from, count) {
        this.updateNotifyPanel(`${from} gifted ${count} subscriptions`)
        this.follow_audio.play();
    }

    claimReward(from, rewardName) {
        this.updateNotifyPanel(`${from} claimed ${rewardName}!`);
        this.follow_audio.play();
    }

    listFollowers() {
        var followers = ""
        this.state.follows.forEach((who)=> {
            followers += `// ${who} `
        })
        return followers;
    }

    listFollowSubs() {
        var txt = ""
        this.state.subs.forEach((who)=> {
            txt += `// Sub: ${who} `
        })
        this.state.follows.forEach((who)=> {
            txt += `// Follow: ${who} `
        })
        return txt;
    }

    listSubs() {
        var subs = ""
        this.state.subs.forEach((who)=> {
            subs += `// ${who} `
        })
        return subs;
    }

    simString() {
        const ias = (this.state.ias || 0).toFixed();
        const gs = (this.state.gs || 0).toFixed();
        const vs = (this.state.vs || 0).toFixed();
        const alt = (this.state.alt || 0).toFixed();
        const heading = (this.state.heading || 0).toFixed();
        const oat = (this.state.oat || 0).toFixed() ;
        const fuel = ((100.0*(this.state.fuel_quant/this.state.fuel_cap)) || 0).toFixed();
        return `IAS: ${ias} kts GS: ${gs} kts VS: ${vs} fpm ALT: ${alt} ft HDG: ${heading}° FUEL: ${fuel}% OAT ${oat}°C`
    }

    
    render() {
        return (
            <div className="overlay">
                <div id="top_scroller">
                    <TopScroller txt={this.state.simconnected?this.simString():"Sim offline"}/>
                </div>
                <div >
                    <Notifier txt={this.state.notifymsg}/>
                </div>
                <div id="bottom_scroller">
                    <BottomScroller txt={this.listFollowSubs()}/>
                </div>
            </div>
        )
    }
}

const domContainer = document.querySelector('#alert_root');
const ee = React.createElement;
ReactDOM.render(ee(Alerts), domContainer);
