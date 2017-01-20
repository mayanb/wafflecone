import 'react-toolbox/lib/commons.scss';
import React from 'react';
import ReactDOM from 'react-dom';
import {Table, TableList} from './Tables.jsx';
import $ from 'jquery';
import MaterialSelect from './Inputs.jsx';
import { AppBar } from 'react-toolbox/lib/app_bar';
import { Navigation } from 'react-toolbox/lib/navigation';
import { Link } from 'react-toolbox/lib/link';


// <Multiselect options={this.state.products} placeholder="Filter by product..."/>

class Main extends React.Component {
  constructor() {
    super();

    this.state = {
      taskGroups: {},
      products: {},
    };

  }

  render() {
    return (
      <div>
        <MaterialBar />
        <div className="container">
          <TableList taskGroups={this.state.taskGroups} processes={this.state.processes}/>
        </div>
      </div>
    );
  }

  componentDidMount() {
    var newState = { taskGroups: [], processes: [], products: [] };

    var defs = [];

    defs.push(this.getProcesses(newState));
    defs.push(this.getProducts(newState));
    defs.push(this.getTasks(newState));

    var component = this

    $.when.apply(null, defs).done(function() {
      component.setState(newState)
    });

    // once you get products & processes, then you run
    // for every process, do an ajax call for tasks/?process_type=x
    // on complete, setState (hopefully should only rerender the right part of it??)

    // make page# part of the object. so when the page number changes for a table T,
    // then 
  }

  getTasks(container) {
    var deferred = $.Deferred();

    $.ajax(window.location.origin + "/ics/tasks/")
      .done(function (data) {
        container.taskGroups = splitTasksByProcess(data.results);
        deferred.resolve();
      })

    return deferred.promise()
  }

  getProducts(container) {
    var deferred = $.Deferred();

    $.ajax(window.location.origin + "/ics/products/")
      .done(function (data) {
        container.products = data
        deferred.resolve();
      })

    return deferred.promise()
  }

  getProcesses(container) {
    var deferred = $.Deferred();

    $.ajax(window.location.origin + "/ics/processes/")
      .done(function (data) {
        container.processes = mapifyProcesses(data)
        deferred.resolve();
      })

    return deferred.promise()
  }
}

function mapifyProcesses(processes) {
  var p = {}
  processes.map(function (obj, i) {
    p[obj.id] = obj
  });
  return p
}

function splitTasksByProcess(tasks) {
  var taskGroups = {}
  tasks.map(function (task, i) {
    if (!taskGroups[task.process_type])
      taskGroups[task.process_type] = [];

    taskGroups[task.process_type].push(task);
  });
  return taskGroups;
}

const MaterialBar = () => (
  <AppBar title="Scoop" flat="true">
    <Navigation type="horizontal">
    </Navigation>
  </AppBar>
);


const Navbar = () => (
  <div className="navbar">
    <h1> Task Log </h1>
  </div>
)

ReactDOM.render(
  <Main />,
  document.getElementById('root')
);