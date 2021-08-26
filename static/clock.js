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

const domContainer = document.querySelector('#clock');
const e = React.createElement;
ReactDOM.render(e(Clock), domContainer);