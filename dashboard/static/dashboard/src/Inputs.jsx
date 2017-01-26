import React from 'react';
import ReactDOM from 'react-dom';
import Select from 'react-select';
import Datepicker from './Datepicker.jsx'
import WrapMenu from './WrapMenu.jsx'
import $ from 'jquery';
import {display} from './Task.jsx'

var getOptions = function(input, callback) {
    if (input.length < 2) {
      callback(null, { optionss: [] })
    } else {
      $.get(window.location.origin + "/ics/tasks/?limit&label=" + input).done(function (data) {
        var options = data.results.map(function (x) {
          return { value: x.id, label: display(x)}
        })
        callback(null, {options : options, complete: false})
      })
    }
  }

class TaskSelect extends React.Component {
  constructor() {
    super();
    this.handleChange = this.handleChange.bind(this);
    this.state = {}

  }

  handleChange(value) {
    var v;
    if (value != undefined && value != null && value.length != 0)
      v = value
    else v = {value: ""}

    this.setState(v)
    this.props.onChange(v)
  };

  render () {
    return (
      <div className="multiselect">
        <Select.Async
          name="form-field-name"
          value={this.state.value}
          loadOptions={getOptions}
          onChange={this.handleChange}
          placeholder={this.props.placeholder}
        />
      </div>
    );
  }


}

class Multiselect extends React.Component {

 constructor() {
    super();
    this.handleMultipleChange = this.handleMultipleChange.bind(this);
    this.state = {
      value: [],
    };

  }

  handleMultipleChange(value) {
    this.props.onChange(value)
    this.setState({value: value});
  };

  render () {
    return (
      <div className="multiselect">
        <Select multi
          name="form-field-name"
          value={this.state.value}
          options={this.getSelect(this.props.options)}
          onChange={this.handleMultipleChange}
          placeholder={this.props.placeholder}
          clearable={false}
        />
      </div>
    );
  }

  getSelect(options) {
    if (!options)
      return;

    return Object.keys(options).map(function (key, i) {
      return {value: options[key].id, label: options[key].name}
    })

  }

}

class Filters extends React.Component {

  constructor() {
    super();
    this.handleInventoryChange = this.handleInventoryChange.bind(this);
    this.handleProcessChange = this.handleProcessChange.bind(this);
    this.handleProductChange = this.handleProductChange.bind(this);
    this.handleDateRangeChange = this.handleDateRangeChange.bind(this);
    this.handleParentChange = this.handleParentChange.bind(this);
    this.handleChildChange = this.handleChildChange.bind(this);
    this.state = {
      inventory: false,
      processes: [],
      products: [],
      parent: "",
      start: "",
      end: ""
    }
  }

  handleInventoryChange() {
    this.setState({inventory: !this.state.inventory })
  }

  handleProcessChange(val) {
    this.setState({processes: val})
  }

  handleProductChange(val) {
    this.setState({products: val})
  }

  handleDateRangeChange(val) {
    this.setState(val)
  }

  handleParentChange(val) {
    this.setState({parent: val.value})
  }

  handleChildChange(val) {
    this.setState({child: val.value})
  }

  render () {
    return (
      <div className="filters">
        <div className="inputs">

          <div className="input-col">
            <div>
              <h1>By process:</h1>
              <Multiselect options={this.props.processes} placeholder="All processes" onChange={(val) => this.handleProcessChange(val)}/>
            </div>

            <div>
              <h1>By origin:</h1>
              <Multiselect options={this.props.products} placeholder="All products" onChange={(val) => this.handleProductChange(val)}/>
            </div>

            <div>
              <h1>By operation date:</h1>
              <Datepicker onChange={(val) => this.handleDateRangeChange(val)} />              
            </div>

            <div>
              <button onClick={() => this.props.onFilter(this.state)}>Filter</button>
            </div>
          </div>

          <div className="input-col">
            <div>
              <h1>By parent:</h1>
              <TaskSelect placeholder="eg. R-CVB-1012" onChange={(val) => this.handleParentChange(val)} />
            </div>

            <div>
              <h1>By child:</h1>
              <TaskSelect placeholder="eg. R-CVB-1012" onChange={(val) => this.handleChildChange(val)} />
            </div>

            <div>
              <input type="checkbox" onChange={this.handleInventoryChange} value={this.state.inventory} />
              <span> Show current inventory </span>
            </div>
          </div>

        </div>
      </div>
    );
  }
}

export { Filters };