Customer Credit Management for Odoo
===================================
A nice solution for managing customer credit limit.

Features:
---------
1. Individual credit limit v.s. global credit limit for every partner(company type);
2. Support partner with childern partner(s): all ; Compute credit&debit using account app.
3. Allow partner to override any credit;
4. Include/exclude uninvoiced amount(from sale orders);
5. New user role to approve/disapprove the sale order with state of account_review.
6. Configurable behavior of sale orders of over-limit partner: 
    raising an exception directly or leaving to the concerned role.

Validate steps:
---------------
1. See if we 'Use Global Limit'. If yes, choose the global credit limit as partner's credit limit.
2. See if the partner has an individual credit limit. If yes, choose the individual credit limit  as partner's credit limit.
3. See if we 'Include Uninvoiced Amount', if yes, we add all unvoiced amount to this partner's credit limit.
4. See if we simply raise an exception or set the sale order's state to 'account_review'

