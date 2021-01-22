import React from 'react';
import { MemoryRouter, Switch, Route } from 'react-router-dom';

import Container from 'react-bootstrap/Container';
import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card'
import CardGroup from 'react-bootstrap/CardGroup'
import { LinkContainer } from 'react-router-bootstrap';
import BootstrapSwitchButton from 'bootstrap-switch-button-react'
import io from "socket.io-client"; // need version 2.1.1 to work with flask

import './App.css';

import logo from './img/logo.png';
import header_left from "./img/cumulus-cloud-left.jpg"
import header_center from "./img/cumulus-cloud-center.jpg"
import header_right from "./img/cumulus-cloud-right.jpg"
//------------------------------------------------------------------------------
const StatusCard = (props) => 
  <Card>
  <Card.Img variant="top" src={header_left} />
  <Card.Body>
    <Card.Title>Status</Card.Title>
    <Card.Text>
    <table border="0">

    <tr><td>Date</td><td>{props.status.date}</td></tr>
    <tr><td>Time</td><td>{props.status.time}</td></tr>
    <tr><td>state</td><td>{props.status.appstate}</td></tr>
    <tr><td>uptime</td><td>{props.status.uptime}</td></tr>
    <tr><td>&nbsp;</td></tr>

    <tr><td>Lat</td><td>{props.gps.lat}</td></tr>
    <tr><td>Lon</td><td>{props.gps.lon}</td></tr>
    <tr><td>Alt</td><td>{props.gps.alt}</td></tr>
    <tr><td>Status</td><td>{props.gps.status}</td></tr>
    <tr><td>Sats</td><td>{props.gps.SatCount}</td></tr>
    <tr><rd>&nbsp;</rd></tr>

    { Object.entries(props.sensors).map( ([key, value]) => <tr><td>{key}</td><td>{value}</td></tr> )}
    <tr></tr>
    </table>
    </Card.Text>
  </Card.Body>
  <Card.Footer>
  <Button variant="outline-danger" size="sm" onClick={props.onPreFlight}>Clear Folders</Button>{' '}
  </Card.Footer>
  </Card>


//------------------------------------------------------------------------------
const TimersCard = (props) => {
  var timer_rows =  Object.keys(props.timers).map((name)=>{ return <tr>
    <td>{name}</td>
    <td><BootstrapSwitchButton  checked={props.timers[name]}
                                width={75}
                                onChange={(val)=>{props.onChange(name, val)}}
                                />{' '}
    <Button variant="outline-primary" onClick={()=>{props.onClick(name)}}>Trigger</Button></td>
  </tr>})
  return <>
  <Card>
  <Card.Img variant="top" src={header_center} />
  <Card.Body>
    <Card.Title>Timers</Card.Title>
    <Card.Text>
      <table border="0">
      {timer_rows}
      </table>
    </Card.Text>
  </Card.Body>
  <Card.Footer>
    <Button variant="outline-primary" size="sm" onClick={props.onDisableAll}>Disable All</Button>{' '}
  </Card.Footer>
  </Card>
  </>
}

//------------------------------------------------------------------------------
const ImagingCard = (props) =>
  <Card>
  <Card.Img variant="top" src={header_right} />
  <Card.Body>
    <Card.Title>Images</Card.Title>
    <Card.Text>
      <img src='/imaging' width="320px"/>
    </Card.Text>
  </Card.Body>
  <Card.Footer>
    <Button variant="outline-primary" size="sm" onClick={props.onSnapshot}>recapture</Button>{' '}
  </Card.Footer>
  </Card>

//------------------------------------------------------------------------------
class Home extends React.Component {

    constructor(props) {
        super(props)
        this.state = { timers: {} ,
                        sensors: {},
                        gps:{},
                        status:{ }
                        }
    }

    componentDidMount(){
        this.socket = io.connect("/");
        this.socket.on('connect', ()=>{console.log("connected")});
        this.socket.on('status', (data)=>{ this.setState({'status':data}) });
        this.socket.on('timers', (data)=>{ this.setState({'timers':data}) });
        this.socket.on('gps', (data)=>{ this.setState({'gps':data}) });
        this.socket.on('sensors', (data)=>{ this.setState({'sensors':data}) });
        this.socket.on('debug', (data)=>{ console.log(data) });
        this.socket.on('disconnect', ()=>{console.log("disconnected")});
    }

    render(){
        return <CardGroup>
          <StatusCard status={this.state.status}
                        gps={this.state.gps}
                        sensors={this.state.sensors}
                        onPreFlight = {()=>{
                            fetch('/cmnd?cmnd=prefilght')
                              .then(response => response.text())
                              .then(data => console.log(data));
                          }}
                        />
          <TimersCard timers={this.state.timers}
                      onChange={(name, value)=>{ this.socket.emit("timer",{ name, value}); }}
                      onClick={(name)=>{ this.socket.emit("trigger", name);}}
                      onDisableAll={()=>{ this.socket.emit("timer",{ name:'*', value:false}); }}
                      />
          <ImagingCard onSnapshot={()=>{this.socket.emit("trigger", 'Snapshot');}} />
        </CardGroup>
    }
  }

//------------------------------------------------------------------------------
const About = () => <span>About</span>;

//------------------------------------------------------------------------------
const App = () => (
  <MemoryRouter>
    <Container className="p-3">
      <table><tr><td><img src={logo}/></td>
      <td>
      <h1>Balloon Mission Controller</h1>
      <h3>4X6UB-11</h3>
      </td></tr></table>
      <br/>
      <Switch>
        <Route path="/about">
          <About />
        </Route>
        <Route path="/">
          <Home />
        </Route>
      </Switch>

    </Container>
  </MemoryRouter>
);

export default App;
