import React from "react";

export default function Logo(props: React.HTMLAttributes<HTMLImageElement> & { className?: string }) {
  return <img src="/images/solace-logo.svg" alt="Solace-AI" className={props.className} />;
}