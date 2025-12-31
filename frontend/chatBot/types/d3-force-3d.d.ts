declare module 'd3-force-3d' {
  export * from 'd3-force';
  export function forceSimulation(nodes?: any[]): any;
  export function forceManyBody(): any;
  export function forceCenter(x?: number, y?: number, z?: number): any;
  export function forceLink(links?: any[]): any;

  export function forceZ() {
    throw new Error('Function not implemented.');
  }
}
