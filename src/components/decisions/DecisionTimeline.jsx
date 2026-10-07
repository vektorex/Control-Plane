export default function DecisionTimeline() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <div className="border-l-2 border-gray-700 pl-4 space-y-6">
                <div>
                    <p className="text-sm text-gray-500">Today, 10:45 AM</p>
                    <p className="text-white font-medium">Decision Requested</p>
                </div>
                <div>
                    <p className="text-sm text-gray-500">Today, 10:46 AM</p>
                    <p className="text-white font-medium">Evidence Collected (12 sources)</p>
                </div>
                <div>
                    <p className="text-sm text-gray-500">Today, 10:46 AM</p>
                    <p className="text-red-400 font-medium">State: Blocked</p>
                </div>
            </div>
        </div>
    );
}