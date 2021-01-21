import React from 'react';
import { MemoryRouter, Switch, Route } from 'react-router-dom';

import Container from 'react-bootstrap/Container';
import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card'
import CardGroup from 'react-bootstrap/CardGroup'
import { LinkContainer } from 'react-router-bootstrap';
import BootstrapSwitchButton from 'bootstrap-switch-button-react'

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
    <tr><td>Lat</td><td>{props.status.gps.lat}</td></tr>
    <tr><td>Lon</td><td>{props.status.gps.lon}</td></tr>
    <tr><td>Alt</td><td>{props.status.gps.alt}</td></tr>
    <tr><td>Status</td><td>{props.status.gps.status}</td></tr>
    <tr><td>Sats</td><td>{props.status.gps.sats}</td></tr>
    <tr><rd>&nbsp;</rd></tr>
    <tr><td>Temp out</td><td>{props.status.sensors.tempout}</td></tr>
    <tr><td>Temp in</td><td>{props.status.sensors.tempin}</td></tr>
    <tr><td>Barometer</td><td>{props.status.sensors.barometer}</td></tr>
    <tr><td>Battery</td><td>{props.status.sensors.battery}</td></tr>
    <tr></tr>
    </table>
    </Card.Text>
  </Card.Body>
  <Card.Footer>
  <Button variant="outline-danger" size="sm">Clear Folders</Button>{' '}
  </Card.Footer>
  </Card>


//------------------------------------------------------------------------------
const TimersCard = (props) => {
  var timer_rows =  Object.keys(props.timers).map((name)=>{ return <tr>
    <td>{name}</td>
    <td><BootstrapSwitchButton checked={props.timers[name]} width={75} onChange={(val)=>{props.onChange(name, val)}}/>{' '}
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
    <Button variant="outline-primary" size="sm">Disable All</Button>{' '}
  </Card.Footer>
  </Card>
  </>
}

//------------------------------------------------------------------------------
const ImagingCard = () => 
  <Card>
  <Card.Img variant="top" src={header_right} />
  <Card.Body>
    <Card.Title>Images</Card.Title>
    <Card.Text>
      <img src='/imaging' width="320px"/>
    </Card.Text>
  </Card.Body>
  <Card.Footer>
    <Button variant="outline-primary" size="sm">recapture</Button>{' '}
  </Card.Footer>
  </Card>

//------------------------------------------------------------------------------
const Home = () => {
    const timers = {
                  'BUZZER':true, 
                  'PLAY-SSDV':false, 
                  'PLAY-SSTV': false, 
                  'APRS': true, 
                  'APRS-META': true, 
                  'Capture': false, 
                  'Snapshot':false, 
                  'Imaging':true
                }
    const status = {
      date : "2021-01-06",
      time : "12:34",
      gps : {
        lat: "32.23",
        lon: "34.56",
        alt: 123
      },
      sensors : {
        tempout : 17.2,
        tempin : -2,
        barometer : 1000,
        battery : 3.4
      }
    }
    return <CardGroup>
      <StatusCard status={status}/>
      <TimersCard timers={timers} 
                  onChange={(name, value)=>{console.log(name, value);}}
                  onClick={(name)=>{console.log("trigger", name);}}
                  />
      <ImagingCard/>
    </CardGroup>
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
{/*
          Navigate to{' '}
          <ButtonToolbar className="custom-btn-toolbar">
            <LinkContainer to="/">
              <Button>Home</Button>
            </LinkContainer>
            <LinkContainer to="/about">
              <Button>About</Button>
            </LinkContainer>
            <LinkContainer to="/users">
              <Button>Users</Button>
            </LinkContainer>
          </ButtonToolbar>
*/}
    </Container>
  </MemoryRouter>
);

export default App;
