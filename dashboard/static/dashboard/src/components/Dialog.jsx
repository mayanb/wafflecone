import React from 'react'

function Dialog(props) {
  return (
    <div className="dialog-shim">
      <div className="dialog-box">
        {props.children}
      </div>
    </div>
  )
}

export {Dialog}