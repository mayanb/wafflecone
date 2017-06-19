import React from 'react'
import ReactDOM from 'react-dom'
import {Link, NavLink} from 'react-router-dom'
import {Dropdown} from 'react-toolbox/lib/dropdown'

var teams = [
    { value: '1', label: 'Bama Production'},
    { value: '5', label: 'Valencia Production' },
    { value: '7', label: 'United Cold'},
    {value: '3', label: 'Fulfillment'},
];

function getTeam() {
  return window.localStorage.getItem("team") || "1"
}

class Topbar extends React.Component {
  constructor(props) {
    super(props)
    this.state = { team: getTeam() }
  }

  handleTeamChange(nt) {
    this.setState({team : nt})
    window.localStorage.setItem("team", nt)
    window.location.reload()
  }

  render () {
    return (
      <div className="d-top">
        <div className="nav-brand">SCOOP</div>
          <div className="nav-team">
          <Dropdown
            source={teams}
            onChange={(val) => this.handleTeamChange(val)}
            value={this.state.team}
          />
          </div>
      </div>
    )
  }
}

class Navbar extends React.Component {

  constructor(props) {
    super(props)
    this.state = { team: getTeam() }
  }

  render () {
    let options = ["Activity Log", "Inventory", "Zebra labels", "Dymo labels", "Settings", "Task View"]
    let links = ["", "inventory", "labels", "dymo", "settings", "task"]

    var navbarSizeClass = "bigNav"
    if (this.props.match.params.id && this.props.match.params.section == "inventory") {
      navbarSizeClass = "littleNav"
    }

    return (
      <div className={"d-nav " + navbarSizeClass}>
        <Link to={"/dashboard/" + (this.props.match.params.section||"") + "/"} style={{"display":(navbarSizeClass=="littleNav")?"":"none"}}>
          <div className="pushout">
          </div>
        </Link>
        <div className="bar">
          <div>
          <ul>
            { 
              options.map(function (x, i) {
                return (
                <li key={i}> 
                  <NavLink exact to={ "/dashboard/" + links[i]} activeClassName={"active"}>{x}</NavLink>
                </li>
                )
            }, this )}
          </ul>
          </div>
        </div>
      </div>
    )
  }
}

const ContentDescriptor = (props) => (
	<div className="content-descriptor">
		<div className="left">
			<p style={{ display: (props.count > 0)?"":"none" }}> Showing {props.startIndex}-{props.startIndex+props.count} results out of {props.total}. </p>
			<p style={{ display: (props.count > 0)?"none":"" }}> Looks like there's nothing here! Try changing your filters. </p>
		</div>
		<div className="right">
			<button style={{ display: props.previous?"":"none" }} onClick = { () => props.onPage(props.previous) }>Previous</button>
			<button style={{ display: props.next?"":"none" }} onClick = {() => props.onPage(props.next) }>Next</button>
		</div>
	</div>
)

export {Navbar, ContentDescriptor, Topbar}