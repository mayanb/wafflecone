import React from 'react'
import ReactDOM from 'react-dom'
import {getCookie, csrfSafeMethod} from './csrf.jsx'
import {BrowserRouter as Router, Route} from 'react-router-dom'
import $ from 'jquery'
import moment from 'moment'

import {Navbar} from './Layout.jsx'
import Tasks from './Tasks.jsx'
import FactoryMap from './FactoryMap.jsx'
import LabelPrinter from './LabelPrinter.jsx'
import Inventory from './Inventory2.jsx'

class Main extends React.Component {
  constructor() {
    super();

    this.state = { selectedInventory: 2 }
  }

  componentDidMount() {

    // handle cross-site forgery request stuff
    let csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
      beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
      }
    })
  }

  render () {
    return (
      <Router>
          <div>
          <div className="parent">
            <main className="d-content">
              <Route exact path={"/dashboard/"} component={ActivityLog} />
              <Route path={"/dashboard/inventory/"} component={Invent} />
              <Route path={"/dashboard/labels/"} component={LabelPrinter} />
              <Route path={"/dashboard/settings/"} component={FactoryMap} />
            </main>
            <Navbar 
              className="d-nav" 
              options={["Dashboard", "Activity Log", "Inventory", "Labels", "Settings"]}
              links={["dsda", "", "inventory", "labels", "settings"]}
              shrink={this.state.selectedInventory}
            ></Navbar>
            <aside className="d-ads"></aside>
          </div>
          </div>
      </Router>
    )
  }
}


function ActivityLog(props) {
  return (
    <Tasks inventory={false} filters={getFilters()} />
  )
}

function Invent(props) {
  return (
    <Inventory inventory={true} filters={getFilters()} />
  )
}




// QUERY STRING STUFF

function QueryStringToJSON() {            
    var pairs = location.search.slice(1).split('&');
    
    var result = {};
    pairs.forEach(function(pair) {
        pair = pair.split('=');
        let key = pair[0]
        if (key && key != "") {
          result[key] = decodeURIComponent(pair[1] || '');
          if (key.toLowerCase() == "processes" || key.toLowerCase() == "products") {
            result[key] = result[key].split(',')
          }
        }
    });

    return JSON.parse(JSON.stringify(result));
}

function getFilters() {
  let filters = QueryStringToJSON()
  //filters.label = {value: filters.label}
  if (!filters || (Object.keys(filters).length === 0 && filters.constructor === Object)) {
    return { active: 1, start: moment(new Date()).format("YYYY-MM-DD").toString(), end: moment(new Date()).format("YYYY-MM-DD").toString() }
  }
  return filters
}

ReactDOM.render(
  <Main />,
  document.getElementById('root')
);
