import React, { Component } from 'react';
import { OpenSheetMusicDisplay as OSMD } from 'opensheetmusicdisplay';

class OpenSheetMusicDisplay extends Component {
    constructor(props) {
      super(props);
      this.state = { dataReady: false };
      this.osmd = undefined;
      this.divRef = React.createRef();
    }
  
    async setupOsmd() {
      const options = {
        backend: 'svg',
        autoResize: this.props.autoResize !== undefined ? this.props.autoResize : true,
        drawTitle: this.props.drawTitle !== undefined ? this.props.drawTitle : false,
        drawSubtitle: false,
        drawPartNames: false,
        pageBackgroundColor: 'transparent',
        disableCursor: false,
        cursorsOptions: [{
          type: 1,
          color: "#EA384D",
          alpha: 0.9,
          follow: true,
          thickness: 4
        }]
      }
      
      console.log('Creating OSMD with options:', options);
      this.osmd = new OSMD(this.divRef.current, options);
      
      console.log('Loading MusicXML...');
      await this.osmd.load(this.props.file);
      
      console.log('Rendering OSMD...');
      await this.osmd.render();
      
      console.log('OSMD rendered, cursor state:', {
        cursor: this.osmd.cursor,
        isVisible: this.osmd.cursor?.isVisible,
        cursorElement: this.osmd.cursor?.cursorElement
      });
      
      // Reset and show cursor once
      this.osmd.cursor.reset();
      this.osmd.cursor.show();
      
      // Configure cursor behavior
      if (this.osmd.cursor) {
        this.osmd.cursor.autoMoveToNextNote = false;
        this.osmd.cursor.autoMoveToNextMeasure = false;
      }
      
      
      console.log('Cursor after show:', {
        isVisible: this.osmd.cursor?.isVisible,
        cursorElement: this.osmd.cursor?.cursorElement,
        autoMoveToNextNote: this.osmd.cursor?.autoMoveToNextNote
      });
      
      this.props.onReady?.(this.osmd);
    }
  
    resize = () => {
      this.forceUpdate();
    }

  
    shouldComponentUpdate(nextProps) {
      return nextProps.file !== this.props.file || 
             nextProps.drawTitle !== this.props.drawTitle || 
             nextProps.autoResize !== this.props.autoResize;
    }
  
    componentWillUnmount() {
      window.removeEventListener('resize', this.resize)
    }
  
    componentDidUpdate(prevProps) {
      if (this.props.file !== prevProps.file) {
        this.setupOsmd();
      }
    }
  
    // Called after render
    componentDidMount() {
      this.setupOsmd();
      window.addEventListener('resize', this.resize);
    }
  
    render() {
      return (<div ref={this.divRef} />);
    }
  }

  export default OpenSheetMusicDisplay;