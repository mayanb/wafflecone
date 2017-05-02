import React from 'react';
import ReactDOM from 'react-dom';
import moment from 'moment';
import {Dialog} from 'react-toolbox/lib/dialog'
import {display, toCSV} from './Task.jsx';

export default function ProcessDialog(props) {
  let actions = []

  return (
    <Dialog
      actions={actions}
      active={props.active}
      onEscKeyDown={props.onProcessClose}
      onOverlayClick={props.onProcessClose}
      title={""}
    >
      <DialogContents process={props.process} />
    </Dialog>
  )

}

class DialogContents extends React.Component {
  constructor(props) {
    super(props)
    this.onAttributeChange = this.onAttributeChange.bind(this)
  }