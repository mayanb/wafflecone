import React from 'react'
import ReactDOM from 'react-dom'
import {getCookie, csrfSafeMethod} from './csrf.jsx'
import {BrowserRouter as Router, Route} from 'react-router-dom'
import $ from 'jquery'
import moment from 'moment'
import ZebraPrinter from './ZebraPrinter.jsx'
import {Navbar, Topbar} from './Layout.jsx'
import FactoryMap from './FactoryMap.jsx'
import LabelPrinter from './LabelPrinter.jsx'
import Inventory from './Inventory2.jsx'
import Task from './Task-2.jsx'
import Activity from './ActivityLog-2.jsx'
import Dash from './Dash.jsx'
//import NewAccount from './NewAccount.jsx'

class Main extends React.Component {
  constructor() {
    super();
    this.handleExpandRequest = this.handleExpandRequest.bind(this)
    this.handleShrinkRequest = this.handleShrinkRequest.bind(this)
    this.state = { shrink: false }
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

  handleExpandRequest() {
    this.setState({ shrink: true})
  }

  handleShrinkRequest() {
    this.setState({ shrink: false})
  }

  render () {
    return (
      <Router>
        <div>
          <div className="parent">
            <main className="d-content">
              <Route exact path={"/dashboard/dash/"} component={Dash} />
              <Route exact path={"/dashboard/"} component={Activity} />
              <Route path={"/dashboard/inventory/:id?"} component={Inventory} />
              <Route path={"/dashboard/labels/"} component={ZebraPrinter} />
              <Route path={"/dashboard/zebra/"} component={ZebraPrinter} />
              <Route path={"/dashboard/dymo/"} component={LabelPrinter} />
              <Route path={"/dashboard/settings/"} component={FactoryMap} />
              <Route path={"/dashboard/task/:id?"} component={Task} />
              <Route path={"/dashboard/settings"} component={Settings} />
            </main>

            <Route path="/dashboard/:section?/:id?" component={Navbar} />
            <aside className="d-ads"></aside>
          </div>
          <Route path="/dashboard/:section?/:id?" component={Topbar} />
        </div>
      </Router>
    )
  }
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

// console.log(window.location.pathname)
// if (window.location.pathname == "/dashboard/newaccount/") {
//   ReactDOM.render(
//     <NewAccount />, document.getElementById('root')
//   )
// } else {
//   ReactDOM.render(
//     <Main />,
//     document.getElementById('root')
//   );
// }

  ReactDOM.render(
    <Main />,
    document.getElementById('root')
  );
