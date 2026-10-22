/**
 * May this compiled contract be reviewed, and if not, why not.
 *
 * Kept apart from both the adapter and the component because it is a decision
 * rather than a shape. Two rules drive it:
 *
 * The interface must never offer a review control for something the server
 * would refuse - an enabled button that always fails teaches nothing about the
 * gate it belongs to.
 *
 * And when it withholds the control it must say which refusal applies. A
 * control that silently disappears reads as a bug, and the reason *is* the
 * lesson: reviewing confirms a clean compile was read, so it cannot settle an
 * open question and cannot vouch for bytes that disagree with their own hash.
 */

function plural(count, one, many) {
  return count === 1 ? one : many;
}

export function reviewability(entry) {
  if (!entry) {
    return { reviewable: false, reason: "No review material for this bounty." };
  }

  if (entry.humanReviewed) {
    return {
      reviewable: false,
      reason:
        "A person has already recorded reading this contract. Reviewing it "
        + "again would prove nothing further.",
    };
  }

  // Order matters below: an unresolved question is what a blocked contract is
  // actually waiting on, so it is named before anything else that is wrong.
  const unresolved = (entry.resolutions || []).filter((item) => !item.resolved);
  if (unresolved.length) {
    return {
      reviewable: false,
      reason:
        `${unresolved.length} ${plural(unresolved.length, "question", "questions")} must be `
        + "settled before this can compile clean. Reviewing does not resolve "
        + "ambiguity - it only confirms a clean compile was read.",
    };
  }

  const mismatched = (entry.documents || []).filter((doc) => !doc.hashAgrees);
  if (mismatched.length) {
    return {
      reviewable: false,
      reason:
        `${mismatched.length} stored ${plural(mismatched.length, "document does", "documents do")} `
        + `not match the hash ${plural(mismatched.length, "it", "they")} declared. `
        + "Reading them proves nothing until that is resolved.",
    };
  }

  if (!(entry.documents || []).length) {
    return {
      reviewable: false,
      reason: "No stored source documents. There is nothing here to have read.",
    };
  }

  return { reviewable: true, reason: "" };
}
