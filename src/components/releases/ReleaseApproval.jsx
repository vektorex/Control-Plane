export default function ReleaseApproval() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <p className="text-gray-400 mb-4">Required approvals (HITL STEP 18):</p>
            <div className="p-4 bg-gray-900 rounded border border-gray-700 flex justify-between items-center">
                <span className="text-white">Security Review</span>
                <span className="text-green-400">Approved by @secops</span>
            </div>
        </div>
    );
}