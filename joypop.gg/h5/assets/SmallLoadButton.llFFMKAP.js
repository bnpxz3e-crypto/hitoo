import{k as p,w as h,l as B,L as d,A as C,y as n,M as s,O as S,r,c as M,P as c,g as w}from"./vue-vendor.C7q8trD7.js";import{_ as x}from"./index.BAR33Wf_.js";const E=["disabled"],G=["stroke"],L=p({__name:"SmallLoadButton",props:{loading:{type:Boolean,default:!1},disabled:{type:Boolean,default:!1},customStyle:{default:()=>({})},loadingColor:{default:""},hideGlobalMask:{type:Boolean,default:!1},overlay:{type:Boolean,default:!1},toCircle:{type:Boolean,default:!1}},emits:["click"],setup(t,{emit:u}){const o=t,m=u,f=r(null),l=r(null),v=w(),b=M(()=>o.customStyle),k=()=>{if(l.value)return;const e=document.createElement("div");e.id="global-loading-mask-"+(v?.uid??""),e.style.cssText=`
    position: fixed;
    top: 0;
    inset-inline-start: 0;
    width: 100vw;
    height: 100vh;
    z-index: 2147483647;
    background-color: transparent;
    pointer-events: auto;
    touch-action: none;
  `,e.addEventListener("touchmove",y=>y.preventDefault(),{passive:!1}),(document.querySelector("#mobile-overlay-root")||document.querySelector("#mobile-app")||document.body).appendChild(e),l.value=e},i=()=>{l.value?.parentNode&&(l.value.parentNode.removeChild(l.value),l.value=null)};h(()=>[o.loading,o.overlay],([e,a])=>{e?a&&!o.hideGlobalMask&&k():i()},{immediate:!0}),B(()=>{i()});const g=e=>{o.loading||o.disabled||m("click",e)};return(e,a)=>(c(),d("button",{ref_key:"btnRef",ref:f,class:n(["small-load-button is-btn",{"is-loading":t.loading,"is-to-circle":t.toCircle,"is-disabled":t.disabled}]),style:C(b.value),disabled:t.disabled||t.loading,onClick:g},[s("div",{class:n(["btn-content content-loading",{"is-visible":t.loading}])},[(c(),d("svg",{class:"loading-icon",viewBox:"0 0 24 24",fill:"none",stroke:t.loadingColor||"currentColor","stroke-width":"2.5","stroke-linecap":"round","stroke-linejoin":"round"},[...a[0]||(a[0]=[s("path",{d:"M21 12a9 9 0 1 1-6.219-8.56"},null,-1)])],8,G))],2),s("div",{class:n(["btn-content content-default",{"is-visible":!t.loading}])},[S(e.$slots,"default",{},void 0,!0)],2)],14,E))}}),q=x(L,[["__scopeId","data-v-165066ee"]]);export{q as S};
