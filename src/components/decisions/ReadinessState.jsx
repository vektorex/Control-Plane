export default function ReadinessState() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">Recent Assessments</h2>
            <div className="space-y-4">
                <div className="p-4 bg-gray-900 rounded-lg border border-gray-800 flex justify-between">
                    <div>
                        <p className="font-medium text-white">Workflow Execution: wf-12345</p>
                        <p className="text-sm text-gray-500 mt-1">Checked 2 mins ago</p>
                    </div>
                    <span className="px-3 py-1 h-fit bg-red-900/50 text-red-400 border border-red-800 rounded text-sm font-medium">Blocked</span>
                </div>
                <div className="p-4 bg-gray-900 rounded-lg border border-gray-800 flex justify-between">
                    <div>
                        <p className="font-medium text-white">Solution Deployment: sol-98765</p>
                        <p className="text-sm text-gray-500 mt-1">Checked 1 hour ago</p>
                    </div>
                    <span className="px-3 py-1 h-fit bg-green-900/50 text-green-400 border border-green-800 rounded text-sm font-medium">Ready</span>
                </div>
            </div>
        </div>
    );
}