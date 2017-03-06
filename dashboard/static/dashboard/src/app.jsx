import React from 'react';
import ReactDOM from 'react-dom';
import { Navbar} from './Layout.jsx'
import Tasks from './Tasks.jsx'
import FactoryMap from './FactoryMap.jsx'
import LabelPrinter from './LabelPrinter.jsx'
import moment from 'moment'
import $ from 'jquery'

function SectionHeader(props) {
  return (
    <div className="section-header">
      <i className="material-icons">{props.icon}</i>
      <h1>{props.title}</h1>
    </div>
  );
}

class Main extends React.Component {
  constructor() {
    super();
    this.refresh = this.refresh.bind(this)
    this.state = {
      active: -1,
      filters: getFilters()
    };

  }

  componentDidMount() {

    // inventory, dashboard, or settings??

    let csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
      beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
      }
    })


    var str = window.location.pathname
    if (str.lastIndexOf("/") == str.length - 1) {
      str = str.substr(0, str.length-1)
    }

    var pieces = str.split("/")
    let piece = pieces[pieces.length - 1]
    if (piece == "" || piece == "dashboard")
      this.setState({active: 1})
    else if (piece == "inventory")
      this.setState({active: 2})
    else if (piece == "labels")
      this.setState({active: 3})
    else if (piece == "settings")
      this.setState({active: 4})

    // also, check if there are pre-existing filters
    window.addEventListener("popstate", this.refresh)
  }

  refresh(e) {
    console.log("filters being set")
    this.setState({filters: e.state})
  }

  render() {
    var obj = false

    if (this.state.active == 1 || this.state.active == 2)
      obj = <Tasks inventory={(this.state.active==2)} filters={this.state.filters} />

    else if (this.state.active == 3) {
      obj = <LabelPrinter />
    }

    else if (this.state.active == 4) {
      obj = <FactoryMap />
    }

    return (
      <div className="parent">
          <Navbar 
            options={["Activity Log", "Inventory", "Labels", "Settings"]}
            links={["", "inventory", "labels", "settings"]} 
            active={this.state.active} 
            onNav={ (x) => this.setState({active: x}) }
          />
          {obj}
      </div>
    );
  }

  handleNav(x) {
    if (x > 1) {
      return
    }
    this.setState({active: x})
  }

}

ReactDOM.render(
  <Main />,
  document.getElementById('root')
);

function QueryStringToJSON() {            
    var pairs = location.search.slice(1).split('&');
    
    var result = {};
    pairs.forEach(function(pair) {
        pair = pair.split('=');
        if (pair[0] && pair[0] != "")
          result[pair[0]] = decodeURIComponent(pair[1] || '');
    });

    return JSON.parse(JSON.stringify(result));
}

function getFilters() {
  let filters = QueryStringToJSON()
  if (!filters || (Object.keys(filters).length === 0 && filters.constructor === Object)) {
    return { active: 1, start: moment(new Date()).format("YYYY-MM-DD").toString(), end: moment(new Date()).format("YYYY-MM-DD").toString() }
  }
  return filters
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = $.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}