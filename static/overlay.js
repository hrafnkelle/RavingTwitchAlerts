'use strict';

Number.prototype.pad = function(n) {
    if (n==undefined)
        n = 2;

    return (new Array(n).join('0') + this).slice(-n);
}


class Clock extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
        time: this.timeString()
    };
  }

  componentDidMount() {
    this.intervalID = setInterval(
      () => this.tick(),
      1000
    );
  }

  componentWillUnmount() {
    clearInterval(this.intervalID);
  }

  timeString() {
      var now = new Date();
      return `${now.getUTCHours().pad()}:${now.getUTCMinutes().pad()}:${now.getUTCSeconds().pad()}`;
  }
  tick() {
    this.setState({
      time: this.timeString()
    });
  }

  render() {
    return (
        <h1><img src="clock_small.png"/> {this.state.time} <img src="gpsicon_small.png"/> Iceland</h1>
    );
  }
}

class Alerts extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            event: null,
            follows: Array(5)
        }
        this.socket = new WebSocket('wss://' + window.location.hostname +'/ws');
    }
    audio = new Audio('/overlay/follower_chord.wav');

    componentDidMount() {
        this.socket.onmessage = (data) => {
            console.dir(data.data);
            
            var event = JSON.parse(data.data)
            if (event.subscription.type == 'channel.follow')
                this.newFollow(event.event.user_name)
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
        this.audio.play();
    }

    render() {
        var followers = ""
        this.state.follows.forEach((who)=> {
            followers += `// ${who} `
        })
        return (
            <h1>Latest follows: {followers}</h1>
        )
    }
}

const domContainer = document.querySelector('#clock');
const e = React.createElement;
ReactDOM.render(e(Clock), domContainer);

const domContainer2 = document.querySelector('#bottom_scroller');
const ee = React.createElement;
ReactDOM.render(ee(Alerts), domContainer2);
