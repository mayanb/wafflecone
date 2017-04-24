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
    let params = {
      limit: true,
      ordering: '-created_at',
      label: input,
      team: window.localStorage.getItem("team") || "1"
    }
    $.get(window.location.origin + "/ics/tasks/search/", params).done(function (data) {
      var options = data.results.map(function (x) {
        return { value: x.id, label: x.display}
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
      <div className="multiselect filters inputs">
        <i className="material-icons">search</i>
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

  componentWillReceiveProps(nextProps) {
    if (nextProps.value != this.state.value) {
      this.setState({value: nextProps.value })
    }
  }

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

class InventoryFilter extends React.Component {
  render() {
    return (
    <div className="filters inputs">
      <Select multi
        options={this.props.options} 
        value={this.props.selected} 
        placeholder="All products" 
        labelKey="code"
        valueKey="code"
        onChange={(val) => this.props.onFilter("productFilter", val)}
      />
    </div>
    )
  }
}

class Filters extends React.Component {

  constructor(props) {
    super(props);
    this.handleChange = this.handleChange.bind(this);
    this.handleDateRangeChange = this.handleDateRangeChange.bind(this);
    this.state = {
      start: "",
      end: "",
      active: 1
    }
  }

  componentWillReceiveProps(nextProps) {
    if (this.props.dates != nextProps.dates) {
      this.setState( {
      processes: [],
      products: [],
      parent: "",
      start: "",
      end: "",
      active: 1})
    }
  }

  handleChange(which, payload) {
    this.props.onFilter({[which] : payload })
  }

  handleDateRangeChange(date) {
    this.props.onFilter(date)
  }

  render () {

    var obj = false

    if (this.props.dates) {
      obj = <div><Datepicker initialDates={this.props.initialDates} onChange={this.handleDateRangeChange} /></div>
    }

    return (
      <div className="filters inputs">
        <div>
          <TaskSelect placeholder="All tasks" value={this.props.label} onChange={(val) => this.handleChange("label", val)} />
        </div>

        <div>
          <Multiselect options={this.props.processes} value={this.props.filters.processes} placeholder="All processes" onChange={(val) => this.handleChange("processes", val)}/>
        </div>

        <div>
          <Multiselect options={this.props.products} value={this.props.filters.products} valueArray={this.props.filters.products} placeholder="All products" onChange={(val) => this.handleChange("products", val)}/>
        </div>

        {obj}

      </div>
    );
  }
}

export { Filters, InventoryFilter, TaskSelect };