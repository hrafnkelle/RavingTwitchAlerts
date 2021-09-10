'use strict';

function BottomScroller(props) {
    return (
        <h1>Latest followers: {props.txt}</h1>
    );
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
            notifymsg : null
        }
        this.timerId = null;
        this.socket = new WebSocket('wss://' + window.location.hostname +'/ws');
    }
    follow_audio = new Audio('follower_chord.wav');
    raid_audio = new Audio('raid.wav');

    componentDidMount() {
        this.socket.onmessage = (data) => {
            console.dir(data.data);
            
            var event = JSON.parse(data.data)
            if (event.subscription.type == 'channel.follow')
                this.newFollow(event.event.user_name)
            else if (event.subscription.type == 'channel.raid')
                this.raid(event.event.from_broadcaster_user_name, event.event.viewers)
            else if (event.subscription.type == 'channel.subscribe')
                this.subscribe(event.event.user_name, event.event.tier)
            else if (event.subscription.type == 'channel.cheer')
                this.cheer(event.event.user_name, event.event.bits)
            else if (event.subscription.type == 'channel.subscription.gift') {
                if(event.event.is_anonymous)
                    this.cheer("Anonymous", event.event.bits)
                else
                    this.cheer(event.event.user_name, event.event.total)
            }
            else {
                console.log(`Unknown event ${event.subscription.type}`)
            }
        }
    }

    componentWillUnmount() {
        this.socket.send('close');
        this.socket.close();
    }

    newFollow(name) {
        var currFollows = this.state.follows
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
        this.updateNotifyPanel(`${from} subscribed at ${tier} tier`)
        this.follow_audio.play();
    }

    gifted(from, count) {
        this.updateNotifyPanel(`${from} gifted ${count} subscriptions`)
        this.follow_audio.play();
    }

    listFollowers() {
        var followers = ""
        this.state.follows.forEach((who)=> {
            followers += `// ${who} `
        })
        return followers;
    }
    
    render() {
        return (
            <div className="overlay">
                <div >
                    <Notifier txt={this.state.notifymsg}/>
                </div>
                <div id="bottom_scroller">
                    <BottomScroller txt={this.listFollowers()}/>
                </div>
            </div>
        )
    }
}

const domContainer = document.querySelector('#alert_root');
const ee = React.createElement;
ReactDOM.render(ee(Alerts), domContainer);
