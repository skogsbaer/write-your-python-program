import * as path from 'path';
import * as Mocha from 'mocha';
import * as glob from 'glob';

export async function run() {
	// Create the mocha test
	const mocha = new Mocha({
		ui: 'tdd',
		color: true
	});

	const testsRoot = path.resolve(__dirname, '..');

	const files = await glob.glob('**/**.test.js', { cwd: testsRoot });
	files.forEach(f => mocha.addFile(path.resolve(testsRoot, f)));
	try {
		// Run the mocha test
		mocha.run(failures => {
			if (failures > 0) {
				throw new Error(`${failures} tests failed.`);
			}
		});
	} catch (err) {
		console.error(err);
		throw err;
	}
}
