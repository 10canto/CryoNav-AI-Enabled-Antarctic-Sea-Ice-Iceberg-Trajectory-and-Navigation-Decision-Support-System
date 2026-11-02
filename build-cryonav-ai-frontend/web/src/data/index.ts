import type { DataSource, SourceKind } from './DataSource';
import { DemoSource } from './DemoSource';
import { LiveSource } from './LiveSource';

export const demoSource = new DemoSource();
export const liveSource = new LiveSource();

export function getSource(kind: SourceKind): DataSource {
  return kind === 'demo' ? demoSource : liveSource;
}
